/* Host-only query storage and assertions around extracted production functions. */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "amd_family.h"
#include "amdgpu_asic_addr.h"
#include "amdgfxregs.h"
#define UNREACHABLE(msg) do { fprintf(stderr,"unreachable: %s\n",msg);abort(); } while(0)
#define MAX2(a,b) ((a) > (b) ? (a) : (b))
struct radeon_info {
   enum radeon_family family;
   enum amd_gfx_level gfx_level;
   struct { unsigned ver_major, ver_minor, ver_rev, num_queues; } ip[AMD_NUM_IP_TYPES];
   unsigned pci_id, pci_rev_id, vce_harvest_config, family_id, chip_external_rev, chip_rev;
   enum vcn_version vcn_ip_version;
   enum vpe_version vpe_ip_version;
   enum sdma_version sdma_ip_version;
   enum rt_version rt_ip_version;
   unsigned max_se, cik_macrotile_mode_array[16], max_render_backends, num_tcc_blocks, l2_cache_size;
   bool is_amdgpu;
};
struct drm_amdgpu_info_device { unsigned device_id, pci_rev, vce_harvest_config, family, external_rev, chip_rev, num_rb_pipes; };
#include "actual_graphics.inc"
static unsigned checks;
#define CHECK(x) do { checks++; if(!(x)) { fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);return 1; } } while(0)
int main(void) {
   for (unsigned rev=1;rev<255;rev++) {
      struct radeon_info info={0}; info.ip[AMD_IP_GFX].ver_major=7;
      struct drm_amdgpu_info_device dev={.family=FAMILY_KV,.external_rev=rev,.device_id=0x9920,.num_rb_pipes=4};
      enum radeon_family expected=rev<0x61?CHIP_KAVERI:rev<0x71?CHIP_LIVERPOOL:rev<0x81?CHIP_GLADIUS:CHIP_KABINI;
      CHECK(ac_identify_chip(&info,&dev)); CHECK(info.family==expected); CHECK(info.gfx_level==GFX7);
      CHECK(ac_get_gfx_level(info.family)==GFX7); CHECK(info.pci_id==dev.device_id); CHECK(info.chip_external_rev==rev);
   }
   const struct { unsigned family,rev;enum radeon_family expected;unsigned gfx; } controls[]={
      {FAMILY_CI,0x14,CHIP_BONAIRE,7},{FAMILY_CI,0x28,CHIP_HAWAII,7},{FAMILY_SI,0x05,CHIP_TAHITI,6},{FAMILY_VI,0x14,CHIP_TONGA,8}};
   for(unsigned i=0;i<sizeof(controls)/sizeof(controls[0]);i++) {
      struct radeon_info info={0}; info.ip[AMD_IP_GFX].ver_major=controls[i].gfx;
      struct drm_amdgpu_info_device dev={.family=controls[i].family,.external_rev=controls[i].rev};
      CHECK(ac_identify_chip(&info,&dev)); CHECK(info.family==controls[i].expected);CHECK((unsigned)ac_get_gfx_level(info.family)==(unsigned)info.gfx_level);
   }
   CHECK(ac_get_gfx_level(CHIP_LIVERPOOL)==GFX7); CHECK(ac_get_gfx_level(CHIP_GLADIUS)==GFX7);
   CHECK(strcmp(ac_get_family_name(CHIP_LIVERPOOL),"LIVERPOOL")==0); CHECK(strcmp(ac_get_family_name(CHIP_GLADIUS),"GLADIUS")==0);
   CHECK(strcmp(ac_get_llvm_processor_name(CHIP_LIVERPOOL),"bonaire")==0); CHECK(strcmp(ac_get_llvm_processor_name(CHIP_GLADIUS),"bonaire")==0);
   CHECK(ac_get_gs_table_depth(GFX7,CHIP_LIVERPOOL)==32);CHECK(ac_get_gs_table_depth(GFX7,CHIP_GLADIUS)==32);
   CHECK(ac_get_gs_table_depth(GFX7,CHIP_KAVERI)==16);CHECK(ac_get_gs_table_depth(GFX9,CHIP_NAVI21)==-1);
   const struct { enum radeon_family family;unsigned raster,raster1,se,rb; } layouts[]={
      {CHIP_LIVERPOOL,0x2a00161a,0,2,4},{CHIP_GLADIUS,0x2a00161a,0x2e,4,8},
      {CHIP_KAVERI,2,0,1,2},{CHIP_BONAIRE,0x16000012,0,2,4},{CHIP_HAWAII,0x3a00161a,0x2e,4,16}};
   for(unsigned i=0;i<sizeof(layouts)/sizeof(layouts[0]);i++) {
      struct radeon_info info={.family=layouts[i].family,.max_se=layouts[i].se,.is_amdgpu=true,.num_tcc_blocks=8};
      unsigned raster=~0u,raster1=~0u,repeat=0;ac_get_raster_config(&info,&raster,&raster1,&repeat);
      CHECK(raster==layouts[i].raster);CHECK(raster1==layouts[i].raster1);CHECK(repeat!=0);CHECK((repeat&(repeat-1))==0);
      struct drm_amdgpu_info_device dev={.num_rb_pipes=layouts[i].rb}; rb_class(&info,&dev);CHECK(info.max_render_backends==layouts[i].rb);
      cache_class(&info);CHECK(info.l2_cache_size==8*1024u*(info.family==CHIP_HAWAII?64u:128u));
   }
   struct radeon_info kaveri={.family=CHIP_KAVERI};struct drm_amdgpu_info_device bad_old={.num_rb_pipes=4};
   rb_class(&kaveri,&bad_old);CHECK(kaveri.max_render_backends==2);
   unsigned raster,raster1;ac_get_raster_config(&kaveri,&raster,&raster1,NULL);CHECK(raster==0);CHECK(raster1==0);
   printf("PASS %u assertions: KV revision sweep, family/GFX7/LLVM, GS/cache/backend and raster controls\n",checks);return 0;
}
