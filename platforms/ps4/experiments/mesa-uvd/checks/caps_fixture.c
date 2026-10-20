/* SPDX-License-Identifier: MIT
 * Focused CPU check of the actual patched Mesa ac_video.c; no GPU operations.
 */
#include "ac_gpu_info.h"
#include "ac_linux_drm.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

struct ac_drm_device { unsigned unused; };
struct kernel_cap { uint32_t valid, max_width, max_height, max_pixels_per_frame, max_level, pad; };
static struct kernel_cap decode[8], encode[8];
static int decode_error, encode_error;
static unsigned decode_queries, encode_queries, cases;

_Static_assert(CHIP_BONAIRE < CHIP_LIVERPOOL && CHIP_LIVERPOOL < CHIP_GLADIUS &&
               CHIP_GLADIUS < CHIP_KAVERI && CHIP_KAVERI < CHIP_TONGA &&
               CHIP_GLADIUS < CHIP_POLARIS10 && CHIP_GLADIUS < CHIP_STONEY &&
               CHIP_GLADIUS < CHIP_VEGA10, "PS4 must remain within legacy GFX7 thresholds");

int ac_drm_query_video_caps_info(struct ac_drm_device *dev, unsigned type, unsigned size, void *ptr)
{
   (void)dev;
   assert(size == sizeof(decode));
   /* Even plausible data returned alongside an error must never enable PS4. */
   if (type == AMDGPU_INFO_VIDEO_CAPS_DECODE) {
      decode_queries++;
      memcpy(ptr, decode, size);
      return decode_error;
   }
   assert(type == AMDGPU_INFO_VIDEO_CAPS_ENCODE);
   encode_queries++;
   memcpy(ptr, encode, size);
   return encode_error;
}

const char *ac_get_ip_type_string(const struct radeon_info *info, enum amd_ip_type ip)
{
   (void)info; (void)ip;
   return "test";
}

static struct radeon_info initial(enum radeon_family family)
{
   struct radeon_info info = {0};
   info.family = family;
   info.ip[AMD_IP_UVD].num_queues = 1;
   info.ip[AMD_IP_UVD].ver_major = 4;
   info.ip[AMD_IP_UVD].ver_minor = 2;
   /* Deliberately stale advertisements must not survive the PS4 branch. */
   memset(&info.video_caps, 0xff, sizeof(info.video_caps));
   memset(decode, 0, sizeof(decode));
   memset(encode, 0xff, sizeof(encode));
   decode[3] = (struct kernel_cap){1, 1920, 1088, 1920 * 1088, 41, 0};
   decode_error = encode_error = 0;
   decode_queries = encode_queries = 0;
   return info;
}

static void none(const struct radeon_info *info)
{
   struct ac_video_caps zero = {0};
   assert(memcmp(&info->video_caps, &zero, sizeof(zero)) == 0);
}

static void avc(const struct radeon_info *info, uint32_t width, uint32_t height, uint32_t level)
{
   const struct ac_video_dec_codec_caps *cap = &info->video_caps.dec[AC_VIDEO_CODEC_AVC];
   assert(cap->supported && cap->ip_type == AMD_IP_UVD);
   assert(cap->formats.nv12 && cap->formats.value == 1);
   assert(cap->tiers == AC_VIDEO_DEC_TIER0);
   assert(cap->min_width == 64 && cap->min_height == 64);
   assert(cap->max_width == width && cap->max_height == height && cap->max_level == level);
   assert(cap->max_dpb_slots == 17 && cap->max_active_refs == 16);
   assert(cap->bitstream_size_alignment == 128 && cap->bitstream_address_alignment == 256);
   for (unsigned i = 0; i < AC_VIDEO_CODEC_DEC_MAX; i++)
      if (i != AC_VIDEO_CODEC_AVC) assert(!info->video_caps.dec[i].supported);
   for (unsigned i = 0; i < AC_VIDEO_CODEC_ENC_MAX; i++) assert(!info->video_caps.enc[i].supported);
   assert(!info->video_caps.proc.supported);
   for (unsigned i = 0; i < AMD_NUM_IP_TYPES; i++) {
      if (i == AMD_IP_UVD) assert(info->video_caps.queue[i].dec && !info->video_caps.queue[i].enc &&
                                  !info->video_caps.queue[i].proc);
      else assert(!info->video_caps.queue[i].supported);
   }
}

static void run(struct radeon_info *info)
{
   struct ac_drm_device dev = {0};
   ac_fill_video_info(info, &dev);
   cases++;
}

static void ps4_cases(enum radeon_family family)
{
   struct radeon_info info = initial(family);
   run(&info); avc(&info, 1920, 1088, 11);
   assert(decode_queries == 1 && encode_queries == 1);

   info = initial(family); info.ip[AMD_IP_UVD].num_queues = 0;
   run(&info); none(&info); assert(!decode_queries && !encode_queries);

   info = initial(family); decode_error = -22;
   run(&info); none(&info); assert(decode_queries == 1 && encode_queries == 0);

   info = initial(family); encode_error = -5;
   run(&info); none(&info); assert(decode_queries == 1 && encode_queries == 1);

   info = initial(family); decode[3].valid = 0;
   run(&info); none(&info);

   const uint32_t bad[] = {0, 63};
   for (unsigned i = 0; i < 2; i++) {
      info = initial(family); decode[3].max_width = bad[i]; run(&info); none(&info);
      info = initial(family); decode[3].max_height = bad[i]; run(&info); none(&info);
   }
   const uint32_t bad_level[] = {0, 9};
   for (unsigned i = 0; i < 2; i++) {
      info = initial(family); decode[3].max_level = bad_level[i]; run(&info); none(&info);
   }
   info = initial(family); decode[3] = (struct kernel_cap){1, 128, 96, 128 * 96, 30, 0};
   run(&info); avc(&info, 128, 96, 7);

   info = initial(family); decode[3] = (struct kernel_cap){1, 64, 64, 4096, 10, 0};
   run(&info); avc(&info, 64, 64, 0);

   info = initial(family); decode[3] = (struct kernel_cap){1, 7680, 4320, 7680 * 4320, 99, 0};
   run(&info); avc(&info, 1920, 1088, 11);

   info = initial(family); decode[3].max_pixels_per_frame--;
   run(&info); none(&info);
   info = initial(family); decode[3].max_pixels_per_frame = 0;
   run(&info); none(&info);

   info = initial(family); decode[3] = (struct kernel_cap){1, UINT32_MAX, UINT32_MAX, UINT32_MAX, UINT32_MAX, 0};
   run(&info); avc(&info, 1920, 1088, 11);

   info = initial(family);
   for (unsigned i = 0; i < AMD_NUM_IP_TYPES; i++) info.ip[i].num_queues = 1;
   for (unsigned i = 0; i < 8; i++) decode[i].valid = 1;
   info.vcn_ip_version = VCN_5_0_0;
   info.vpe_ip_version = VPE_2_0;
   info.vce_fw_version = 40u << 24;
   run(&info); avc(&info, 1920, 1088, 11);

   info = initial(family); info.ip[AMD_IP_UVD].num_queues = 0;
   info.ip[AMD_IP_VCN_DEC].num_queues = 1; info.vcn_ip_version = VCN_1_0_0;
   run(&info); none(&info);
}

int main(int argc, char **argv)
{
   (void)argv;
   ps4_cases(CHIP_LIVERPOOL);
   ps4_cases(CHIP_GLADIUS);

   if (argc > 1) {
      printf("PASS actual-source PS4 AVC capability checks: %u cases\n", cases);
      return 0;
   }

   /* Existing non-PS4 fallback behavior is untouched by the new branch. */
   struct radeon_info info = initial(CHIP_KAVERI);
   memset(&info.video_caps, 0, sizeof(info.video_caps));
   decode_error = -22;
   run(&info);
   assert(info.video_caps.dec[AC_VIDEO_CODEC_AVC].supported);
   assert(info.video_caps.dec[AC_VIDEO_CODEC_MPEG2].supported);
   assert(info.video_caps.dec[AC_VIDEO_CODEC_VC1].supported);
   assert(!info.video_caps.dec[AC_VIDEO_CODEC_HEVC].supported);
   assert(info.video_caps.dec[AC_VIDEO_CODEC_AVC].max_width == 2048);

   info = initial(CHIP_CARRIZO);
   memset(&info.video_caps, 0, sizeof(info.video_caps));
   decode_error = -22;
   info.ip[AMD_IP_VCE].num_queues = 1; info.vce_fw_version = 40u << 24;
   run(&info);
   assert(info.video_caps.dec[AC_VIDEO_CODEC_HEVC].supported);
   assert(!info.video_caps.dec[AC_VIDEO_CODEC_HEVC].hevc.main10);
   assert(info.video_caps.enc[AC_VIDEO_CODEC_AVC].supported);
   printf("PASS actual-source PS4 AVC capability checks: %u cases\n", cases);
   return 0;
}
