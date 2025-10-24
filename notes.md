# Tracing F1 Generation

Looking for `pairwise_model_f1_balanced`.

healthbench_meta_eval.py:181


healthbench_meta_eval.py:21 - template for the metric name

healthbench_meta_eval.py:134 - __call__() (`model_agreement_metrics <-`)
    healthbench_meta_eval.py:245 - compute_metrics_for_rater_by_class()
        healthbench_meta_eval.py:302 - get_balanced_metrics()


## Findings

On line `healthbench_meta_eval.py:308 - get_balanced_metrics()` there is a `pairwise_model_f1_pos` in the `metrics` dict, but because there is no `pairwise_model_f1_neg` in the dict it does not calculate a balanced version of the metric. So, why is there no negative version? Where do the negative versions come from?

So, all of the `f1` metrics come from `healthbench_meta_eval.py:250 - get_f1_metrics()`. It operates on metrics like "pairwise_model_<recall|precision>_<pos|neg>". It produces an `f1` score for every pair of recall/precision metrics. But, it looks like there is no "pairwise_model_precision_neg" in this function's input. So let's look higher up.

