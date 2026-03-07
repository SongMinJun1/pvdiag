#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd $(dirname $0)/.. && pwd)
TMP=$ROOT/_release_tmp
OUT=$TMP/pvdiag_release
ZIP=$TMP/pvdiag_release.zip

rm -rf $OUT
mkdir -p $OUT/pv_ae
mkdir -p $OUT/research/prognostics
mkdir -p $OUT/docs

cp $ROOT/pv_ae/pv_autoencoder_dayAE.py $OUT/pv_ae/

cp $ROOT/research/prognostics/risk_score.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/add_transition_rankers.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/add_ensemble_rankers.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/run_scores_pipeline.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/weaklabel_eval_2sigma.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/fault_case_study.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/plot_case_timeline.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/ingest_gpvs_faults.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/external_eval_gpvs.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/run_dayae_site.py $OUT/research/prognostics/
cp $ROOT/research/prognostics/README.md $OUT/research/prognostics/

cp $ROOT/docs/DATA_DICTIONARY.md $OUT/docs/
cp $ROOT/docs/score_definition.md $OUT/docs/
cp $ROOT/docs/RELEASE_BOUNDARY.md $OUT/docs/
cp $ROOT/docs/RELEASE_MANIFEST.md $OUT/docs/

rm -f $ZIP
cd $TMP
zip -r pvdiag_release.zip pvdiag_release >/dev/null
cd $ROOT

find $OUT -type f | sort
ls -lh $ZIP
