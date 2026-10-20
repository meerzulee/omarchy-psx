/* SPDX-License-Identifier: MIT
 * Deterministic CPU Mandelbrot renderer. No platform graphics or device API.
 */
#include <errno.h>
#include <math.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PALETTE_SIZE 8192
#define PI 3.14159265358979323846

static unsigned char palette[PALETTE_SIZE][3];

struct view {
    int width, height, threads, max_iter;
    double span, cosine, sine, phase;
    unsigned char *pixels;
};

struct worker {
    struct view *view;
    int index;
};

static void make_palette(void)
{
    /* Midnight, lapis, turquoise, pearl, amber, coral, plum, midnight. */
    static const double stops[][3] = {
        {5, 9, 29}, {21, 55, 129}, {23, 139, 178}, {137, 231, 225},
        {250, 226, 171}, {229, 119, 73}, {124, 47, 112}, {5, 9, 29}
    };
    for (int i = 0; i < PALETTE_SIZE; ++i) {
        double position = 7.0 * i / PALETTE_SIZE;
        int stop = (int)position;
        double t = position - stop;
        t = t * t * (3.0 - 2.0 * t);
        for (int c = 0; c < 3; ++c)
            palette[i][c] = (unsigned char)lround(
                stops[stop][c] * (1.0 - t) + stops[stop + 1][c] * t);
    }
}

static void *render_rows(void *opaque)
{
    const struct worker *worker = opaque;
    const struct view *v = worker->view;
    const double scale = v->span / v->width;
    for (int y = worker->index; y < v->height; y += v->threads) {
        double py = ((v->height - 1) * 0.5 - y) * scale;
        for (int x = 0; x < v->width; ++x) {
            double px = (x - (v->width - 1) * 0.5) * scale;
            double cr = -0.743643887037151 + px * v->cosine - py * v->sine;
            double ci =  0.131825904205330 + px * v->sine + py * v->cosine;
            double q = (cr - 0.25) * (cr - 0.25) + ci * ci;
            int interior = q * (q + cr - 0.25) <= 0.25 * ci * ci ||
                           (cr + 1.0) * (cr + 1.0) + ci * ci <= 0.0625;
            double zr = 0.0, zi = 0.0, zr2 = 0.0, zi2 = 0.0;
            int iteration = 0;
            if (!interior) {
                while (iteration < v->max_iter && zr2 + zi2 <= 256.0) {
                    zi = 2.0 * zr * zi + ci;
                    zr = zr2 - zi2 + cr;
                    zr2 = zr * zr;
                    zi2 = zi * zi;
                    ++iteration;
                }
                interior = iteration == v->max_iter;
            }
            double nx = 2.0 * x / (v->width - 1.0) - 1.0;
            double ny = 2.0 * y / (v->height - 1.0) - 1.0;
            double vignette = 1.0 - 0.10 * (nx * nx + ny * ny);
            unsigned char *pixel = v->pixels + ((size_t)y * v->width + x) * 3;
            if (interior) {
                pixel[0] = 2;
                pixel[1] = 4;
                pixel[2] = (unsigned char)lround(12.0 * vignette);
            } else {
                double mu = iteration + 1.0 - log2(0.5 * log(zr2 + zi2));
                double position = 0.017 * mu + v->phase;
                position -= floor(position);
                int index = (int)(position * PALETTE_SIZE);
                double light = vignette * (0.94 + 0.06 * cos(0.13 * mu));
                for (int c = 0; c < 3; ++c)
                    pixel[c] = (unsigned char)lround(palette[index][c] * light);
            }
        }
    }
    return NULL;
}

static int number(const char *text, int minimum, int maximum)
{
    char *end;
    errno = 0;
    long value = strtol(text, &end, 10);
    if (errno || !*text || *end || value < minimum || value > maximum) {
        fprintf(stderr, "invalid numeric argument\n");
        exit(2);
    }
    return (int)value;
}

int main(int argc, char **argv)
{
    if (argc != 8) {
        fprintf(stderr, "usage: %s WIDTH HEIGHT FIRST COUNT STEP TOTAL THREADS\n", argv[0]);
        return 2;
    }
    int width = number(argv[1], 16, 4096);
    int height = number(argv[2], 16, 2160);
    int first = number(argv[3], 0, 100000);
    int count = number(argv[4], 1, 100000);
    int step = number(argv[5], 1, 100000);
    int total = number(argv[6], 2, 100000);
    int threads = number(argv[7], 1, 32);
    if ((int64_t)first + (int64_t)(count - 1) * step >= total) {
        fprintf(stderr, "requested frame is outside the declared timeline\n");
        return 2;
    }
    size_t bytes = (size_t)width * height * 3;
    unsigned char *pixels = malloc(bytes);
    if (!pixels) {
        fprintf(stderr, "pixel allocation failed\n");
        return 1;
    }
    pthread_t handles[32];
    struct worker workers[32];
    make_palette();
    for (int frame = 0; frame < count; ++frame) {
        int index = first + frame * step;
        double u = (double)index / (total - 1);
        double travel = u - 0.12 * sin(2.0 * PI * u) / (2.0 * PI);
        double angle = 0.11 * u + 0.03 * sin(PI * u);
        struct view view = {
            width, height, threads, 600 + (int)lround(600.0 * u),
            3.7 * exp(log(0.0025 / 3.7) * travel),
            cos(angle), sin(angle), 0.055 * u, pixels
        };
        for (int worker = 0; worker < threads; ++worker) {
            workers[worker] = (struct worker){&view, worker};
            if (pthread_create(&handles[worker], NULL, render_rows, &workers[worker])) {
                fprintf(stderr, "worker creation failed\n");
                return 1;
            }
        }
        for (int worker = 0; worker < threads; ++worker) {
            if (pthread_join(handles[worker], NULL)) {
                fprintf(stderr, "worker join failed\n");
                return 1;
            }
        }
        if (fwrite(pixels, 1, bytes, stdout) != bytes) {
            fprintf(stderr, "RGB output failed: %s\n", strerror(errno));
            return 1;
        }
        if (frame % 30 == 0 || frame + 1 == count)
            fprintf(stderr, "frame=%d/%d timeline=%d span=%.9g iterations=%d\n",
                    frame + 1, count, index, view.span, view.max_iter);
    }
    free(pixels);
    if (fflush(stdout)) {
        fprintf(stderr, "RGB flush failed\n");
        return 1;
    }
    return 0;
}
