/* SPDX-License-Identifier: MIT
 * PS4 UVD readiness observation using AMDGPU INFO ioctls only.
 *
 * Build: cc -std=c11 -O2 -Wall -Wextra -Werror probe-video.c \
 *           $(pkg-config --cflags --libs libdrm) -o probe-video
 * Run:   ./probe-video [/dev/dri/renderD128]
 *
 * Does not initialize VAAPI, allocate GEM/contexts, submit CS, create a UVD
 * session, decode, access debugfs, or request recovery.  Readiness is a
 * point-in-time observation, not a reservation or proof of DMA quiescence.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <xf86drm.h>
#include <amdgpu_drm.h>

static void json_string(const char *s)
{
   putchar('"');
   for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
      if (*p == '"' || *p == '\\') printf("\\%c", *p);
      else if (*p < 32 || *p >= 127) printf("\\u%04x", (unsigned)*p);
      else putchar(*p);
   }
   putchar('"');
}

static uint64_t monotonic_ns(void)
{
   struct timespec now;
   if (clock_gettime(CLOCK_MONOTONIC, &now)) return 0;
   return (uint64_t)now.tv_sec * UINT64_C(1000000000) + (uint64_t)now.tv_nsec;
}

static int info_query(int fd, uint32_t query, uint32_t subtype, void *out, uint32_t size)
{
   struct drm_amdgpu_info req = {0};
   req.return_pointer = (uintptr_t)out;
   req.return_size = size;
   req.query = query;
   if (query == AMDGPU_INFO_VIDEO_CAPS) req.video_cap.type = subtype;
   else req.query_hw_ip.type = subtype;
   if (drmIoctl(fd, DRM_IOCTL_AMDGPU_INFO, &req)) return -errno;
   return 0;
}

static void print_ip(const struct drm_amdgpu_info_hw_ip *ip, int error)
{
   printf("{\"error\":%d,\"major\":%u,\"minor\":%u,\"available_rings\":%u,"
          "\"ib_start_alignment\":%u,\"ib_size_alignment\":%u}",
          error, ip->hw_ip_version_major, ip->hw_ip_version_minor, ip->available_rings,
          ip->ib_start_alignment, ip->ib_size_alignment);
}

static void print_caps(const struct drm_amdgpu_info_video_caps *caps, int error)
{
   printf("{\"error\":%d,\"codecs\":[", error);
   for (unsigned i = 0; i < 8; i++) {
      const struct drm_amdgpu_info_video_codec_info *cap = &caps->codec_info[i];
      printf("%s{\"index\":%u,\"valid\":%u,\"max_width\":%u,\"max_height\":%u,"
             "\"max_pixels_per_frame\":%u,\"max_level\":%u}",
             i ? "," : "", i, cap->valid, cap->max_width, cap->max_height,
             cap->max_pixels_per_frame, cap->max_level);
   }
   printf("]}");
}

int main(int argc, char **argv)
{
   const char *device = argc == 2 ? argv[1] : "/dev/dri/renderD128";
   struct drm_amdgpu_info_hw_ip before = {0}, after = {0};
   struct drm_amdgpu_info_num_handles handles = {0};
   struct drm_amdgpu_info_video_caps decode = {0}, encode = {0};
   int before_error = 0, after_error = 0, handles_error = 0, decode_error = 0, encode_error = 0;
   int open_error = 0, node_type = -1, driver_error = 0;
   bool amdgpu = false, ready = false, free_handle = false, avc_only = false, no_encode = false;
   uint64_t begin = monotonic_ns();
   if (argc > 2 || (argc == 2 && strcmp(argv[1], "--help") == 0)) {
      fprintf(stderr, "Usage: %s [/dev/dri/renderD128]\nQueries only; no decoder session or GPU submission.\n", argv[0]);
      return argc > 2 ? 2 : 0;
   }

   int fd = open(device, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
   if (fd < 0) open_error = -errno;
   else {
      node_type = drmGetNodeTypeFromFd(fd);
      if (node_type == DRM_NODE_RENDER) {
         drmVersionPtr version = drmGetVersion(fd);
         if (!version) driver_error = errno ? -errno : -EIO;
         else {
            amdgpu = version->name && version->name_len == 6 && !memcmp(version->name, "amdgpu", 6);
            drmFreeVersion(version);
         }
         if (amdgpu) {
            before_error = info_query(fd, AMDGPU_INFO_HW_IP_INFO, AMDGPU_HW_IP_UVD, &before, sizeof(before));
            handles_error = info_query(fd, AMDGPU_INFO_NUM_HANDLES, AMDGPU_HW_IP_UVD, &handles, sizeof(handles));
            decode_error = info_query(fd, AMDGPU_INFO_VIDEO_CAPS, AMDGPU_INFO_VIDEO_CAPS_DECODE, &decode, sizeof(decode));
            encode_error = info_query(fd, AMDGPU_INFO_VIDEO_CAPS, AMDGPU_INFO_VIDEO_CAPS_ENCODE, &encode, sizeof(encode));
            after_error = info_query(fd, AMDGPU_INFO_HW_IP_INFO, AMDGPU_HW_IP_UVD, &after, sizeof(after));
            ready = !before_error && !after_error && before.available_rings == 1 && after.available_rings == 1 &&
                    before.hw_ip_version_major == 4 && before.hw_ip_version_minor == 2 &&
                    after.hw_ip_version_major == 4 && after.hw_ip_version_minor == 2;
            free_handle = !handles_error && handles.uvd_max_handles == 1 && !handles.uvd_used_handles;
            const struct drm_amdgpu_info_video_codec_info *avc =
               &decode.codec_info[AMDGPU_INFO_VIDEO_CAPS_CODEC_IDX_MPEG4_AVC];
            avc_only = !decode_error && avc->valid && avc->max_width >= 64 && avc->max_width <= 1920 &&
                       avc->max_height >= 64 && avc->max_height <= 1088 &&
                       avc->max_level >= 10 && avc->max_level <= 41 &&
                       avc->max_pixels_per_frame >= 4096 &&
                       avc->max_pixels_per_frame <= avc->max_width * avc->max_height;
            no_encode = !encode_error;
            for (unsigned i = 0; i < 8; i++) {
               if (i != AMDGPU_INFO_VIDEO_CAPS_CODEC_IDX_MPEG4_AVC && decode.codec_info[i].valid) avc_only = false;
               if (encode.codec_info[i].valid) no_encode = false;
            }
         }
      }
      close(fd);
   }
   bool pass = !open_error && node_type == DRM_NODE_RENDER && amdgpu && ready && free_handle && avc_only && no_encode;
   printf("{\"result\":\"%s\",\"hardware_acceptance\":false,\"decoder_session_created\":false,"
          "\"fence_idle_checked\":false,\"vaapi_profiles_queried\":false,\"device\":",
          pass ? "PASS_READINESS_OBSERVATION" : "FAIL_READINESS_OBSERVATION");
   json_string(device);
   printf(",\"monotonic_begin_ns\":%" PRIu64 ",\"monotonic_end_ns\":%" PRIu64
          ",\"open_error\":%d,\"node_type\":%d,\"driver_error\":%d,\"amdgpu_driver\":%s,\"hw_ip_before\":",
          begin, monotonic_ns(), open_error, node_type, driver_error, amdgpu ? "true" : "false");
   print_ip(&before, before_error);
   printf(",\"handles\":{\"error\":%d,\"supported\":%s,\"max\":%u,\"used\":%u},\"decode\":",
          handles_error, amdgpu && !handles_error ? "true" : "false", handles.uvd_max_handles, handles.uvd_used_handles);
   print_caps(&decode, decode_error);
   printf(",\"encode\":"); print_caps(&encode, encode_error);
   printf(",\"hw_ip_after\":"); print_ip(&after, after_error);
   printf(",\"checks\":{\"ready\":%s,\"free_handle\":%s,\"avc_only\":%s,\"no_encode\":%s}}\n",
          ready ? "true" : "false", free_handle ? "true" : "false", avc_only ? "true" : "false", no_encode ? "true" : "false");
   return pass ? 0 : 1;
}
