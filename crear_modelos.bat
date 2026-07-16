@echo off
echo ============================================
echo CREANDO MODELOS DE IA
echo ============================================

ollama create cualifiquer-intent -f Modelfiles\CualifiquerIntent

ollama create create-product -f Modelfiles\CreateProduct

ollama create increase-detector -f Modelfiles\IncreaseDetector

ollama create attribute-extractor -f Modelfiles\AttributeExtractor

ollama create attribute-classifier -f Modelfiles\AttributeClassifier

ollama create attribute-resolver -f Modelfiles\AttributeResolver

ollama create incomplet-handler -f Modelfiles\IncompletHandler

ollama create general-consultant -f Modelfiles\GeneralConsultant

ollama create create-categories-by-products -f Modelfiles\CreateCategories

echo.
echo ============================================
echo MODELOS CREADOS
echo ============================================

pause