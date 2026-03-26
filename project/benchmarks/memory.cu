#include <cuda_runtime.h>
#include <iostream>
#include <vector>
#include <cstdlib>

#define CHECK_CUDA(call)                                                        \
    do {                                                                        \
        cudaError_t err = (call);                                               \
        if (err != cudaSuccess) {                                               \
            std::cerr << "CUDA error at " << __FILE__ << ":" << __LINE__        \
                      << " - " << cudaGetErrorString(err) << std::endl;         \
            std::exit(EXIT_FAILURE);                                            \
        }                                                                       \
    } while (0)

__global__ void compute_kernel(float* out, size_t n, int inner_iters) {
    size_t idx = static_cast<size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (idx < n) {
        float x = static_cast<float>(idx % 251) * 0.001f + 1.0f;
        float y = 1.0001f;
        #pragma unroll 4
        for (int i = 0; i < inner_iters; ++i) {
            x = x * y + 0.00001f;
            y = y * 1.000001f + 0.000001f;
        }
        out[idx] = x + y;
    }
}

int main(int argc, char** argv) {
    size_t n = 1 << 24;
    int threads_per_block = 256;
    int inner_iters = 4096;
    int iters = 20;

    if (argc > 1) n = static_cast<size_t>(std::stoull(argv[1]));
    if (argc > 2) threads_per_block = std::stoi(argv[2]);
    if (argc > 3) inner_iters = std::stoi(argv[3]);
    if (argc > 4) iters = std::stoi(argv[4]);

    const size_t bytes = n * sizeof(float);
    float* d_out = nullptr;
    CHECK_CUDA(cudaMalloc(&d_out, bytes));

    int blocks = static_cast<int>((n + threads_per_block - 1) / threads_per_block);

    for (int i = 0; i < 5; ++i) {
        compute_kernel<<<blocks, threads_per_block>>>(d_out, n, inner_iters);
    }
    CHECK_CUDA(cudaGetLastError());
    CHECK_CUDA(cudaDeviceSynchronize());

    cudaEvent_t start, stop;
    CHECK_CUDA(cudaEventCreate(&start));
    CHECK_CUDA(cudaEventCreate(&stop));

    CHECK_CUDA(cudaEventRecord(start));
    for (int i = 0; i < iters; ++i) {
        compute_kernel<<<blocks, threads_per_block>>>(d_out, n, inner_iters);
    }
    CHECK_CUDA(cudaGetLastError());
    CHECK_CUDA(cudaEventRecord(stop));
    CHECK_CUDA(cudaEventSynchronize(stop));

    float total_ms = 0.0f;
    CHECK_CUDA(cudaEventElapsedTime(&total_ms, start, stop));
    double avg_ms = static_cast<double>(total_ms) / iters;

    std::vector<float> h_out(std::min<size_t>(n, 1024));
    CHECK_CUDA(cudaMemcpy(h_out.data(), d_out, h_out.size() * sizeof(float), cudaMemcpyDeviceToHost));

    double checksum = 0.0;
    for (float v : h_out) checksum += v;

    std::cout << "benchmark=compute_fma_like" << std::endl;
    std::cout << "n=" << n << std::endl;
    std::cout << "threads_per_block=" << threads_per_block << std::endl;
    std::cout << "inner_iters=" << inner_iters << std::endl;
    std::cout << "iterations=" << iters << std::endl;
    std::cout << "avg_time_ms=" << avg_ms << std::endl;
    std::cout << "checksum_1024=" << checksum << std::endl;

    CHECK_CUDA(cudaEventDestroy(start));
    CHECK_CUDA(cudaEventDestroy(stop));
    CHECK_CUDA(cudaFree(d_out));
    return 0;
}
