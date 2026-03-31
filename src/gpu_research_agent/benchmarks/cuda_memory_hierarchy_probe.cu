#include <cuda_runtime.h>

#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct Options {
  int working_set_kb = 256;
  int stride_bytes = 64;
  int iterations = 20000;
  int threads_per_block = 128;
  int blocks = 80;
  int repeat_count = 3;
  int seed = 7;
};

bool ParseInt(const char* value, int* out) {
  char* end = nullptr;
  long parsed = std::strtol(value, &end, 10);
  if (end == value || *end != '\0') {
    return false;
  }
  *out = static_cast<int>(parsed);
  return true;
}

bool ParseArgs(int argc, char** argv, Options* options) {
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (i + 1 >= argc) {
      return false;
    }
    if (arg == "--working-set-kb") {
      if (!ParseInt(argv[++i], &options->working_set_kb)) return false;
    } else if (arg == "--stride-bytes") {
      if (!ParseInt(argv[++i], &options->stride_bytes)) return false;
    } else if (arg == "--iterations") {
      if (!ParseInt(argv[++i], &options->iterations)) return false;
    } else if (arg == "--threads-per-block") {
      if (!ParseInt(argv[++i], &options->threads_per_block)) return false;
    } else if (arg == "--blocks") {
      if (!ParseInt(argv[++i], &options->blocks)) return false;
    } else if (arg == "--repeat-count") {
      if (!ParseInt(argv[++i], &options->repeat_count)) return false;
    } else if (arg == "--seed") {
      if (!ParseInt(argv[++i], &options->seed)) return false;
    } else {
      return false;
    }
  }
  return true;
}

__global__ void StridedProbeKernel(const std::uint32_t* data,
                                   std::uint64_t* sink,
                                   std::size_t element_count,
                                   std::size_t stride_elems,
                                   int iterations) {
  const std::size_t thread_id = blockIdx.x * blockDim.x + threadIdx.x;
  std::size_t index = thread_id % element_count;
  std::uint64_t acc = 0;

  for (int iter = 0; iter < iterations; ++iter) {
    index = (index + stride_elems) % element_count;
    acc += static_cast<std::uint64_t>(data[index]);
  }

  sink[thread_id] = acc;
}

bool CheckCuda(cudaError_t status, const char* label) {
  if (status == cudaSuccess) {
    return true;
  }
  std::cerr << "{\"error\":\"" << label << ": " << cudaGetErrorString(status) << "\"}" << std::endl;
  return false;
}

}  // namespace

int main(int argc, char** argv) {
  Options options;
  if (!ParseArgs(argc, argv, &options)) {
    std::cerr << "{\"error\":\"invalid_arguments\"}" << std::endl;
    return 2;
  }

  const std::size_t total_bytes = static_cast<std::size_t>(options.working_set_kb) * 1024ULL;
  const std::size_t element_count = std::max<std::size_t>(total_bytes / sizeof(std::uint32_t), 1);
  const std::size_t stride_elems = std::max<std::size_t>(options.stride_bytes / sizeof(std::uint32_t), 1);
  const std::size_t total_threads = static_cast<std::size_t>(options.blocks) * options.threads_per_block;

  std::vector<std::uint32_t> host_data(element_count);
  for (std::size_t i = 0; i < element_count; ++i) {
    host_data[i] = static_cast<std::uint32_t>((i * 2654435761ULL + options.seed) & 0xffffffffu);
  }
  std::vector<std::uint64_t> host_sink(total_threads, 0);

  std::uint32_t* device_data = nullptr;
  std::uint64_t* device_sink = nullptr;
  cudaEvent_t start_event = nullptr;
  cudaEvent_t stop_event = nullptr;

  if (!CheckCuda(cudaMalloc(&device_data, element_count * sizeof(std::uint32_t)), "cudaMalloc(data)")) return 1;
  if (!CheckCuda(cudaMalloc(&device_sink, total_threads * sizeof(std::uint64_t)), "cudaMalloc(sink)")) return 1;
  if (!CheckCuda(cudaMemcpy(device_data, host_data.data(), element_count * sizeof(std::uint32_t), cudaMemcpyHostToDevice),
                 "cudaMemcpy(data)")) return 1;
  if (!CheckCuda(cudaEventCreate(&start_event), "cudaEventCreate(start)")) return 1;
  if (!CheckCuda(cudaEventCreate(&stop_event), "cudaEventCreate(stop)")) return 1;

  float total_elapsed_ms = 0.0f;
  for (int repeat = 0; repeat < options.repeat_count; ++repeat) {
    if (!CheckCuda(cudaMemset(device_sink, 0, total_threads * sizeof(std::uint64_t)), "cudaMemset(sink)")) return 1;
    if (!CheckCuda(cudaEventRecord(start_event), "cudaEventRecord(start)")) return 1;
    StridedProbeKernel<<<options.blocks, options.threads_per_block>>>(device_data, device_sink, element_count, stride_elems,
                                                                      options.iterations);
    if (!CheckCuda(cudaEventRecord(stop_event), "cudaEventRecord(stop)")) return 1;
    if (!CheckCuda(cudaEventSynchronize(stop_event), "cudaEventSynchronize(stop)")) return 1;
    if (!CheckCuda(cudaGetLastError(), "kernel")) return 1;
    float elapsed_ms = 0.0f;
    if (!CheckCuda(cudaEventElapsedTime(&elapsed_ms, start_event, stop_event), "cudaEventElapsedTime")) return 1;
    total_elapsed_ms += elapsed_ms;
  }

  if (!CheckCuda(cudaMemcpy(host_sink.data(), device_sink, total_threads * sizeof(std::uint64_t), cudaMemcpyDeviceToHost),
                 "cudaMemcpy(sink)")) return 1;

  std::uint64_t checksum = 0;
  for (std::uint64_t value : host_sink) {
    checksum ^= value;
  }

  const double avg_elapsed_ms = total_elapsed_ms / std::max(options.repeat_count, 1);
  const double total_touches = static_cast<double>(total_threads) * options.iterations;
  const double total_read_bytes = total_touches * sizeof(std::uint32_t);
  const double bandwidth_gb_s = avg_elapsed_ms > 0.0
                                    ? (total_read_bytes / 1.0e9) / (avg_elapsed_ms / 1000.0)
                                    : 0.0;

  std::ostringstream output;
  output << std::fixed << std::setprecision(6);
  output << "{"
         << "\"benchmark\":\"cuda_memory_hierarchy_probe\","
         << "\"working_set_kb\":" << options.working_set_kb << ","
         << "\"stride_bytes\":" << options.stride_bytes << ","
         << "\"iterations\":" << options.iterations << ","
         << "\"threads_per_block\":" << options.threads_per_block << ","
         << "\"blocks\":" << options.blocks << ","
         << "\"repeat_count\":" << options.repeat_count << ","
         << "\"avg_elapsed_ms\":" << avg_elapsed_ms << ","
         << "\"estimated_bandwidth_gb_s\":" << bandwidth_gb_s << ","
         << "\"checksum\":" << checksum
         << "}";

  std::cout << output.str() << std::endl;

  cudaEventDestroy(start_event);
  cudaEventDestroy(stop_event);
  cudaFree(device_data);
  cudaFree(device_sink);
  return 0;
}
