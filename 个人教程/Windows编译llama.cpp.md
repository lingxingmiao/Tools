# Windows编译llama.cpp
1. 安装 mingw
  1. 下载[mingw](https://link.zhihu.com/?target=https%3A//github.com/niXman/mingw-builds-binaries/releases) x86_64-15.2.0-release-win32-seh-ucrt-rt_v13-rev1.7z
  2. 添加PATH变量 `mingw64\bin`
2. 安装 w64devkit
  1. 下载[w64devkit](https://github.com/skeeto/w64devkit/releases) w64devkit-x86-2.6.0.7z.exe
  2. 添加PATH变量 `w64devkit\bin`
3. 安装 CMake
  1. 安装[CMake](https://cmake.org/download/) cmake-4.3.0-rc3-windows-x86_64.msi
4. 编译 llama.cpp
  1. 克隆llama.cpp `git clone https://github.com/ggerganov/llama.cpp`
  2. 进入llama.cpp `cd llama.cpp/build`
  3. 编译llama.cpp `cmake .. -G "Visual Studio 18 2026" -A x64 -DLLAMA_CURL=OFF`
