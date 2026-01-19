# SkinModel Training Scripts

> SkinModel (공차 분석) 머신러닝 학습 스크립트
> **최종 업데이트**: 2026-01-19

---

## 스크립트 목록

| 파일 | 설명 |
|------|------|
| `implement_skinmodel_ml.py` | ToleranceMLTrainer 클래스 - ML 모델 학습 |
| `upgrade_skinmodel_xgboost.py` | XGBoost 모델 업그레이드 |

---

## 사용법

```bash
cd models/skinmodel-api/training/scripts

# ML 모델 학습
python implement_skinmodel_ml.py --data training_data/ --output models/

# XGBoost 업그레이드
python upgrade_skinmodel_xgboost.py --input models/ --output upgraded/
```

---

*최종 업데이트*: 2026-01-19
