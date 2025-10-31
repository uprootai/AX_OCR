#!/usr/bin/env python3
"""
API bbox 검증 스크립트
"""
import json
import sys

data = json.load(sys.stdin)

print('='*80)
print('📊 API 응답 검증 - bbox 필드 확인')
print('='*80)

# Dimensions 검증
if 'dimensions' in data:
    dims = data['dimensions']
    print(f'\n✅ Dimensions: {len(dims)}개')

    # 처음 5개 검증
    for i, dim in enumerate(dims[:5]):
        print(f'\n📍 D{i}:')
        print(f'  type: {dim.get("type")}')
        print(f'  value: {dim.get("value")} {dim.get("unit")}')

        bbox = dim.get('bbox', {})
        if bbox:
            print(f'  bbox:')
            print(f'    x: {bbox.get("x")}')
            print(f'    y: {bbox.get("y")}')
            print(f'    width: {bbox.get("width")}')
            print(f'    height: {bbox.get("height")}')

            # 필드 검증
            required = ['x', 'y', 'width', 'height']
            has_all = all(k in bbox for k in required)
            status = '✅ 모든 필드 존재!' if has_all else '❌ 누락된 필드'
            print(f'  {status}')
        else:
            print(f'  ❌ bbox 없음')

    # 전체 검증
    print(f'\n🔍 전체 검증:')
    all_have_bbox = all('bbox' in d for d in dims)
    all_complete = all(
        'bbox' in d and
        all(k in d['bbox'] for k in ['x', 'y', 'width', 'height'])
        for d in dims
    )
    status1 = '✅' if all_have_bbox else '❌'
    status2 = '✅' if all_complete else '❌'
    print(f'  모든 dimension에 bbox: {status1}')
    print(f'  모든 bbox에 x,y,w,h: {status2}')

# GD&T 검증
if 'gdt' in data:
    gdt_list = data['gdt']
    print(f'\n✅ GD&T: {len(gdt_list)}개')

    if gdt_list:
        for i, gdt in enumerate(gdt_list[:2]):
            print(f'\n📍 G{i}:')
            print(f'  type: {gdt.get("type")}')
            bbox = gdt.get('bbox', {})
            if bbox:
                required = ['x', 'y', 'width', 'height']
                has_all = all(k in bbox for k in required)
                print(f'  bbox: x={bbox.get("x")}, y={bbox.get("y")}, w={bbox.get("width")}, h={bbox.get("height")}')
                status = '✅' if has_all else '❌'
                print(f'  필드 완전성: {status}')

# 시각화 URL
if 'visualization_url' in data:
    print(f'\n✅ Visualization URL: {data["visualization_url"]}')

print('\n' + '='*80)
print('🎯 검증 결과 요약')
print('='*80)

# 요약
dim_count = len(data.get('dimensions', []))
gdt_count = len(data.get('gdt', []))

dims_with_bbox = sum(1 for d in data.get('dimensions', []) if 'bbox' in d)
dims_with_complete_bbox = sum(
    1 for d in data.get('dimensions', [])
    if 'bbox' in d and all(k in d['bbox'] for k in ['x', 'y', 'width', 'height'])
)

gdts_with_bbox = sum(1 for g in data.get('gdt', []) if 'bbox' in g)
gdts_with_complete_bbox = sum(
    1 for g in data.get('gdt', [])
    if 'bbox' in g and all(k in g['bbox'] for k in ['x', 'y', 'width', 'height'])
)

print(f'\nDimensions:')
print(f'  전체: {dim_count}개')
print(f'  bbox 있음: {dims_with_bbox}개 ({dims_with_bbox}/{dim_count})')
print(f'  완전한 bbox: {dims_with_complete_bbox}개 ({dims_with_complete_bbox}/{dim_count})')

print(f'\nGD&T:')
print(f'  전체: {gdt_count}개')
if gdt_count > 0:
    print(f'  bbox 있음: {gdts_with_bbox}개 ({gdts_with_bbox}/{gdt_count})')
    print(f'  완전한 bbox: {gdts_with_complete_bbox}개 ({gdts_with_complete_bbox}/{gdt_count})')

# 최종 판정
all_dims_ok = dim_count > 0 and dims_with_complete_bbox == dim_count
all_gdts_ok = gdt_count == 0 or gdts_with_complete_bbox == gdt_count

if all_dims_ok and all_gdts_ok:
    print('\n✅ 모든 bbox가 완전한 형식(x, y, width, height)을 가지고 있습니다!')
else:
    print('\n⚠️ 일부 bbox가 불완전합니다.')

print('='*80)
