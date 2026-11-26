# zenoh-pico のサンプルを PC(Linux / macOS / Windows)向けにビルドする。
#
#   cmake -B build
#   cmake --build build
#   ./build/pico_pub -e tcp/127.0.0.1:7447
#
# zenoh-pico 本体は FetchContent で GitHub から取得し、静的ライブラリとして組み込む。
cmake_minimum_required(VERSION 3.16)
project(zenoh_template_pico LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

set(ZENOH_PICO_VERSION "1.10.2" CACHE STRING "取得する zenoh-pico のタグ")

# zenoh-pico 側のオプション。サブプロジェクトとして取り込むとサンプルやテストはビルドされない。
set(BUILD_SHARED_LIBS OFF CACHE BOOL "zenoh-pico を静的ライブラリにする" FORCE)
# 機能の有効・無効も同じように切り替えられる(既定値は zenoh-pico の cmake/feature_config.cmake)
# set(Z_FEATURE_QUERY 0 CACHE STRING "" FORCE)

include(FetchContent)
FetchContent_Declare(
  zenohpico
  GIT_REPOSITORY https://github.com/eclipse-zenoh/zenoh-pico.git
  GIT_TAG ${ZENOH_PICO_VERSION}
  GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(zenohpico)

foreach(app pico_pub pico_sub pico_queryable pico_cmd_vel)
  add_executable(${app} src/${app}.c)
  target_link_libraries(${app} PRIVATE zenohpico::lib)
endforeach()
