#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
default_project_dir="$(cd -- "${script_dir}/.." && pwd)"
project_dir="${1:-${default_project_dir}}"
model_dir="${project_dir}/runtime/models/faster-rcnn-resnet50"
target="${model_dir}/model.pth"
model_url="https://download.pytorch.org/models/fasterrcnn_resnet50_fpn_coco-258fb6c6.pth"
model_size=167502836
model_sha256="258fb6c638b15964ddcdd1ae0748c5eef1be9e732750120cc857feed3faac384"
parallelism="${FASTER_RCNN_DOWNLOAD_CONNECTIONS:-32}"
[[ "${parallelism}" =~ ^[1-9][0-9]*$ ]] || {
  echo "FASTER_RCNN_DOWNLOAD_CONNECTIONS must be a positive integer." >&2
  exit 2
}
parts_dir="${model_dir}/.model.pth.parts-${parallelism}"

mkdir -p "${model_dir}"

if [[ -f "${target}" ]] && echo "${model_sha256}  ${target}" | sha256sum --check --status; then
  echo "Faster R-CNN weights are already present and verified."
  exit 0
fi

mkdir -p "${parts_dir}"
chunk_size=$(((model_size + parallelism - 1) / parallelism))
pids=()

for ((index = 0; index < parallelism; index += 1)); do
  start=$((index * chunk_size))
  ((start < model_size)) || break
  end=$((start + chunk_size - 1))
  ((end < model_size)) || end=$((model_size - 1))
  part="${parts_dir}/$(printf '%03d' "${index}").part"
  expected_size=$((end - start + 1))

  if [[ -f "${part}" ]] && [[ "$(stat -c '%s' "${part}")" -eq "${expected_size}" ]]; then
    continue
  fi

  (
    temporary="${part}.download"
    rm -f "${temporary}"
    curl --fail --location --silent --show-error --retry 8 --retry-delay 2 \
      --range "${start}-${end}" --output "${temporary}" "${model_url}"
    [[ "$(stat -c '%s' "${temporary}")" -eq "${expected_size}" ]]
    mv "${temporary}" "${part}"
  ) &
  pids+=("$!")
done

for pid in "${pids[@]}"; do
  wait "${pid}"
done

assembled="${target}.assembled"
rm -f "${assembled}"
for part in "${parts_dir}"/*.part; do
  cat "${part}" >> "${assembled}"
done

echo "${model_sha256}  ${assembled}" | sha256sum --check
mv "${assembled}" "${target}"
rm -rf "${parts_dir}"
echo "Verified Faster R-CNN weights: ${target}"
