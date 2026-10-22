/* Standalone diagnostic harness. MIT; shader input retains its upstream license. */
#define GL_GLEXT_PROTOTYPES
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GL/glcorearb.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void require(int condition, const char *message)
{
    if (!condition) { fprintf(stderr, "FAIL %s EGL=%x GL=%x\n", message, eglGetError(), glGetError()); exit(2); }
}

static char *read_file(const char *path)
{
    FILE *f = fopen(path, "rb"); require(f != NULL, "open shader");
    require(fseek(f, 0, SEEK_END) == 0, "seek shader");
    long n = ftell(f); require(n > 0 && n < 100000, "shader size");
    rewind(f); char *s = calloc((size_t)n + 1, 1); require(s != NULL, "allocate shader");
    require(fread(s, 1, (size_t)n, f) == (size_t)n, "read shader"); fclose(f); return s;
}

int main(int argc, char **argv)
{
    setvbuf(stderr, NULL, _IONBF, 0);
    require(argc == 2, "usage: tilemax-probe exact-upstream-shader");
    PFNEGLGETPLATFORMDISPLAYEXTPROC get_platform = (PFNEGLGETPLATFORMDISPLAYEXTPROC)eglGetProcAddress("eglGetPlatformDisplayEXT");
    require(get_platform != NULL, "platform display extension");
    EGLDisplay display = get_platform(EGL_PLATFORM_SURFACELESS_MESA, EGL_DEFAULT_DISPLAY, NULL);
    require(display != EGL_NO_DISPLAY && eglInitialize(display, NULL, NULL), "initialize EGL");
    require(eglBindAPI(EGL_OPENGL_API), "bind desktop GL");
    EGLint cfg_attributes[] = {EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT, EGL_NONE};
    EGLConfig config; EGLint count;
    require(eglChooseConfig(display, cfg_attributes, &config, 1, &count) && count == 1, "choose config");
    EGLint ctx_attributes[] = {EGL_CONTEXT_MAJOR_VERSION, 4, EGL_CONTEXT_MINOR_VERSION, 3,
                               EGL_CONTEXT_OPENGL_PROFILE_MASK, EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT, EGL_NONE};
    EGLContext context = eglCreateContext(display, config, EGL_NO_CONTEXT, ctx_attributes);
    require(context != EGL_NO_CONTEXT, "create GL4.3 context");
    require(eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, context), "make current");
    const char *renderer = (const char *)glGetString(GL_RENDERER);
    fprintf(stderr, "RENDERER %s\nVERSION %s\n", renderer, glGetString(GL_VERSION));
    require(renderer && strstr(renderer, "liverpool"), "Liverpool required; reject software/other GPU");

    /* Same WG64/4-pass and 64x36 dispatch geometry as observed 1080p CarChase.
     * Texture contents are deterministic; scene initialization and tessellation
     * are deliberately absent. This tests this shader variant, not the scene.
     */
    const char *prefix = "#version 430 core\n#define K 30\n#define THREAD_COUNT 64\n#define PASS_COUNT 4\n#define MAX_BUFFER_BIND 1\n#define STEP_UV vec2(2.0/1920.0,2.0/1080.0)\nvec2 unpack_velocity(sampler2D t,vec2 uv){return (texture(t,uv).xy-0.5)*0.1;}\n";
    char *body = read_file(argv[1]);
    const GLchar *parts[] = {prefix, body};
    GLuint shader = glCreateShader(GL_COMPUTE_SHADER);
    glShaderSource(shader, 2, parts, NULL); glCompileShader(shader);
    GLint ok = 0; glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
    char log[16384]; GLsizei length;
    glGetShaderInfoLog(shader, sizeof(log), &length, log);
    if (length) fprintf(stderr, "SHADER %s\n", log);
    require(ok, "compile compute shader");
    GLuint program = glCreateProgram(); glAttachShader(program, shader); glLinkProgram(program);
    glGetProgramiv(program, GL_LINK_STATUS, &ok);
    glGetProgramInfoLog(program, sizeof(log), &length, log);
    if (length) fprintf(stderr, "PROGRAM %s\n", log);
    require(ok, "link compute program");

    const size_t output_bytes = 64u * 36u * 2u * sizeof(float);
    GLint alignment; glGetIntegerv(GL_SHADER_STORAGE_BUFFER_OFFSET_ALIGNMENT, &alignment);
    require(alignment > 0 && 4096 % alignment == 0, "SSBO alignment");
    const size_t guard_bytes = 4096, total_bytes = output_bytes + 2 * guard_bytes;
    unsigned char *data = malloc(total_bytes); require(data != NULL, "allocate guards");
    memset(data, 0xa5, total_bytes);
    GLuint buffer; glGenBuffers(1, &buffer); glBindBuffer(GL_SHADER_STORAGE_BUFFER, buffer);
    glBufferData(GL_SHADER_STORAGE_BUFFER, (GLsizeiptr)total_bytes, data, GL_DYNAMIC_DRAW);
    glBindBufferRange(GL_SHADER_STORAGE_BUFFER, 1, buffer, (GLintptr)guard_bytes, (GLsizeiptr)output_bytes);
    const size_t texture_bytes = 1920u * 1080u * 2u;
    unsigned char *pixels = calloc(texture_bytes, 1); require(pixels != NULL, "allocate zero velocity texture");
    GLuint texture; glGenTextures(1, &texture); glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, texture);
    glTexStorage2D(GL_TEXTURE_2D, 1, GL_RG8, 1920, 1080);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 1920, 1080, GL_RG, GL_UNSIGNED_BYTE, pixels);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glUseProgram(program); glUniform1i(glGetUniformLocation(program, "velocity_texture"), 0);
    require(glGetError() == GL_NO_ERROR, "setup GL errors");
    fprintf(stderr, "DISPATCH_BEGIN WG64 grid64x36 iterations200 output_bytes=%zu guard_bytes=%zu\n", output_bytes, guard_bytes);
    for (unsigned i = 0; i < 200; ++i) {
        glDispatchCompute(64, 36, 1);
        glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT);
    }
    glMemoryBarrier(GL_BUFFER_UPDATE_BARRIER_BIT);
    GLsync fence = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0);
    GLenum wait = glClientWaitSync(fence, GL_SYNC_FLUSH_COMMANDS_BIT, 2000000000ull);
    require(wait == GL_ALREADY_SIGNALED || wait == GL_CONDITION_SATISFIED, "bounded GPU completion");
    glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, (GLsizeiptr)total_bytes, data);
    require(glGetError() == GL_NO_ERROR, "readback GL error");
    unsigned errors = 0, guard_errors = 0;
    for (size_t i = 0; i < guard_bytes; ++i) {
        guard_errors += data[i] != 0xa5;
        guard_errors += data[guard_bytes + output_bytes + i] != 0xa5;
    }
    float *output = (float *)(data + guard_bytes);
    for (size_t i = 0; i < output_bytes / sizeof(float); ++i)
        errors += !isfinite(output[i]) || fabsf(output[i] + .05f) > .000001f;
    fprintf(stderr, "ORACLE output_errors=%u guard_errors=%u values=%zu\n", errors, guard_errors, output_bytes / sizeof(float));
    require(!errors && !guard_errors, "output/guard mismatch");
    glDeleteSync(fence); glDeleteTextures(1, &texture); glDeleteBuffers(1, &buffer);
    glDeleteProgram(program); glDeleteShader(shader); free(body); free(data); free(pixels);
    eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroyContext(display, context); eglTerminate(display);
    fprintf(stderr, "PASS_TILEMAX_WG64_200_DISPATCH_ORACLE_ONLY\n"); return 0;
}
