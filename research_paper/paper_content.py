"""Structured content for the BirdVision AI research paper.

Single source of truth consumed by build_pdf.py, build_tex.py and build_docx.py.
Every quantitative claim traces to a repository artifact (metrics.json,
training_history.json, confusion_matrix.npy, classification_report.csv) or to
verified source code; see verification_report.md for the provenance map.

Block grammar (list of tuples):
  ("title", str)
  ("authors", [ {name, dept, org, extra} ... ])
  ("abstract", str)
  ("index", str)
  ("h1", roman, TITLE)
  ("h2", letter, Title)
  ("p", text)                      # [n] = citation, *x* = italic
  ("runin", lead, text)            # italic run-in heading then text
  ("olist", [items])               # numbered list
  ("ulist", [items])
  ("eq", n, img)                   # numbered equation (image in figures/)
  ("fig", label, caption, img, wide)
  ("table", label, caption, header, rows, wide)
"""

TITLE = ("BirdVision AI: An Explainable Transfer-Learning System for "
         "Fine-Grained Bird Species Recognition with Location-Aware "
         "Species Discovery")

AUTHORS = [
    {"name": "Author Name(s) — to be supplied",
     "dept": "Department / Program — to be supplied",
     "org": "Institution — to be supplied",
     "extra": "Contact e-mail — to be supplied"},
]

ABSTRACT = (
    "Automated bird species recognition can lower the expertise barrier for "
    "birdwatchers, students and biodiversity monitoring, but fine-grained "
    "classification among visually similar species remains difficult and a bare "
    "species label is of limited use without supporting context. We present "
    "BirdVision AI, an end-to-end system that pairs a trained convolutional "
    "neural network (CNN) with explainability and location-aware species "
    "discovery. The classifier is an EfficientNetB0 backbone, pre-trained on "
    "ImageNet and transfer-learned on the Caltech-UCSD Birds-200-2011 "
    "(CUB-200-2011) dataset (200 species; 5,194 training, 800 validation and "
    "5,794 held-out test images). On the held-out test set the model attains a "
    "top-1 accuracy of 71.06%, top-5 accuracy of 92.44%, and a macro-averaged "
    "F1 of 0.715; per-class F1 ranges from 0.19 to 0.98 and the dominant errors "
    "occur between congeneric species (e.g. Chipping vs. Tree Sparrow). The CNN "
    "is the sole source of predictions and runs independently of two optional "
    "enrichment services: a Groq-hosted large language model (openai/gpt-oss-"
    "120b) that summarizes the identified species and answers questions, and the "
    "eBird API, which returns recent species-specific observations and nearby "
    "hotspots resolved through verified taxonomy. We integrate Grad-CAM for "
    "visual attribution and report its production behaviour. We emphasise that "
    "the softmax scores are uncalibrated, that a confidence threshold is a "
    "heuristic rather than an out-of-distribution detector, and that no "
    "independent field validation was performed. The system is a functional, "
    "reproducible reference implementation rather than a production-grade or "
    "scientifically validated identification tool."
)

INDEX = ("bird species classification, EfficientNetB0, transfer learning, "
         "fine-grained recognition, explainable AI, Grad-CAM, convolutional "
         "neural networks, biodiversity informatics, eBird.")

BLOCKS = [
    # ===================================================================== I
    ("h1", "I", "INTRODUCTION"),
    ("p",
     "Birdwatching and biodiversity monitoring depend on accurate species "
     "identification, a task that traditionally requires substantial expertise. "
     "Deep convolutional neural networks have driven large gains in image "
     "classification [1], [3], [4] and now underpin ecological applications such "
     "as camera-trap analysis [18] and large-scale species datasets [7]. Applied "
     "to birds, however, recognition is a *fine-grained* problem: hundreds of "
     "species share body plans and differ only in subtle plumage, bill or "
     "structural cues, and intra-class variation from pose, lighting and "
     "background frequently exceeds inter-class variation [6], [8]."),
    ("p",
     "A second limitation is that a species label alone is a thin user "
     "experience. A birdwatcher who learns that a photograph is a particular "
     "warbler usually also wants to know how confident the model is, why it "
     "reached that decision, what the species looks and behaves like, and where "
     "the bird might be observed nearby. Systems that return only a class name "
     "provide none of this and give users no basis for trusting or questioning "
     "the result."),
    ("p",
     "BirdVision AI addresses both concerns with a modular system built around a "
     "genuinely trained classifier. A user uploads a photograph; a FastAPI "
     "backend validates and preprocesses it, runs EfficientNetB0 inference, maps "
     "output indices to the exact training class order, and returns ranked "
     "candidates with an explicit, uncalibrated-confidence disclaimer. Grad-CAM "
     "[11] produces an attribution heatmap. Two optional services enrich the "
     "result without ever participating in classification: a Groq-hosted large "
     "language model summarizes the identified species and answers follow-up "
     "questions, and the eBird API [16] returns recent, species-specific "
     "observations and nearby birding hotspots."),
    ("runin", "Research objectives.",
     "We set out to (i) train and honestly evaluate a transfer-learning "
     "classifier on CUB-200-2011; (ii) preserve exact class-index integrity from "
     "training to inference; (iii) provide production explainability; (iv) add "
     "language-model and citizen-science enrichment as strictly separated, "
     "fail-safe components; and (v) document limitations without inflating "
     "results."),
    ("runin", "Contributions.",
     "This paper makes the following *implemented and verified* contributions:"),
    ("olist", [
        "A reproducible EfficientNetB0 transfer-learning classifier for 200 "
        "bird species with artifact-level integrity checks that validate the "
        "output-unit count against the stored class mapping before serving.",
        "An honest held-out evaluation (top-1 71.06%, top-5 92.44%, macro-F1 "
        "0.715) with per-class analysis and a confusion study that isolates "
        "congeneric failure modes; reported test metrics are independently "
        "recomputed from the saved confusion matrix and match the stored "
        "metrics exactly.",
        "A production Grad-CAM implementation that works with a nested Keras 3 "
        "backbone and includes degenerate-map validation.",
        "A clean architectural separation in which a Groq large language model "
        "and the eBird observation service enrich, but never perform, "
        "classification, each with classified error handling and graceful "
        "degradation.",
    ]),
    ("p",
     "We explicitly distinguish these from *proposed future work* (Section "
     "VII), which includes model calibration, out-of-distribution rejection and "
     "independent field validation; none of these is claimed as implemented."),

    # ==================================================================== II
    ("h1", "II", "RELATED WORK"),
    ("runin", "Deep and fine-grained classification.",
     "Modern image classification rests on deep CNNs trained on ImageNet [2], "
     "with residual connections [3] and compound-scaled architectures such as "
     "EfficientNet [4] improving the accuracy-efficiency trade-off; VGG-style "
     "networks [5] remain common feature extractors. Fine-grained recognition "
     "on datasets like CUB-200-2011 [6] motivated specialised methods, including "
     "bilinear pooling of two CNN feature extractors [8], which reaches 84.1% on "
     "CUB-200-2011 using higher-capacity backbones and domain-specific "
     "fine-tuning."),
    ("runin", "Transfer learning and ecological imagery.",
     "Transferring ImageNet-pretrained features to smaller target domains is "
     "effective because early layers learn general visual primitives [9]. This "
     "underpins ecological applications such as automated wildlife "
     "identification from camera traps [18] and large species benchmarks [7], "
     "where severe class imbalance and visual similarity depress accuracy."),
    ("runin", "Explainability, calibration and reliability.",
     "Grad-CAM [11] and its variants [12] visualise class-discriminative image "
     "regions via gradients of the class score with respect to convolutional "
     "feature maps. Separately, modern networks are often miscalibrated: softmax "
     "outputs do not match empirical correctness frequencies [13], and standard "
     "classifiers assign confident scores to out-of-distribution inputs, "
     "motivating dedicated detection baselines [14]. Dropout [10] is a common "
     "regulariser. These findings frame our deliberate refusal to present raw "
     "softmax scores as calibrated probabilities."),
    ("runin", "Birding information and citizen science.",
     "Acoustic monitoring models such as BirdNET [15] identify species from "
     "sound, a modality orthogonal to our image classifier. The eBird platform "
     "[16] aggregates hundreds of millions of citizen-science observations and "
     "exposes them through a public API, which we use for location-aware "
     "discovery."),
    ("p",
     "Table I situates BirdVision AI among representative studies. Because "
     "datasets, modalities and evaluation protocols differ, the reported figures "
     "are *not* directly comparable and we make no ranking claim; the table "
     "clarifies scope and relevance rather than superiority."),
    ("table", "I",
     "COMPARISON WITH REPRESENTATIVE RELATED WORK (PROTOCOLS DIFFER; NOT "
     "DIRECTLY COMPARABLE)",
     ["Study", "Data / modality", "Architecture", "Task", "Reported"],
     [
        ["Lin et al. [8]", "CUB-200-2011 (image)", "Bilinear VGG", "Fine-grained ID", "84.1% acc."],
        ["Van Horn [7]", "iNaturalist (image)", "Inception/ResNet", "5k-species ID", "~67% top-1"],
        ["Tan&Le [4]", "ImageNet (image)", "EfficientNet-B0", "1k-class ID", "77.1% top-1"],
        ["Kahl et al. [15]", "Audio recordings", "CNN (spectrogram)", "Acoustic ID", "Audio (diff. modality)"],
        ["This work", "CUB-200-2011 (image)", "EfficientNetB0 (TL)", "200-species ID + discovery", "71.06% top-1"],
     ], True),
    ("p",
     "Our aim is not a new state-of-the-art accuracy on CUB-200-2011; the "
     "lightweight EfficientNetB0 backbone and modest fine-tuning budget trail "
     "heavier fine-grained methods [8]. The contribution is an integrated, "
     "honestly-evaluated and explainable system with location-aware enrichment."),

    # =================================================================== III
    ("h1", "III", "DATASET"),
    ("p",
     "The classifier is trained and evaluated on the Caltech-UCSD Birds-200-2011 "
     "(CUB-200-2011) dataset [6], which contains 11,788 images across 200 North-"
     "American-centric bird species. The project configuration records the data "
     "source as a Kaggle mirror listed as \"200 Bird Species with 11,788 "
     "Images\"; inspection of the class labels (CUB folder identifiers of the "
     "form 001.Black_footed_Albatross) confirms that this mirror is CUB-200-2011 "
     "and not a distinct dataset. We therefore report CUB-200-2011 throughout."),
    ("p",
     "The pipeline uses the splits summarised in Table II: 5,194 training, 800 "
     "validation and 5,794 held-out test images, summing to the full 11,788. The "
     "held-out test set is used only for final evaluation. Per-class support in "
     "the test split is near-uniform (mean 29.0 images per class; range 11-30), "
     "so macro- and weighted-averaged metrics are close. The exact assignment "
     "procedure (random versus the official CUB train/test partition) is not "
     "recorded in the available artifacts and is marked for verification."),
    ("table", "II", "DATASET AND SPLIT SUMMARY (CUB-200-2011)",
     ["Partition", "Images", "Classes", "Mean/class"],
     [
        ["Training", "5,194", "200", "26.0"],
        ["Validation", "800", "200", "4.0"],
        ["Test (held-out)", "5,794", "200", "29.0"],
        ["Total", "11,788", "200", "-"],
     ], False),
    ("p",
     "Input images are converted to RGB and resized to 224x224. Pixel values are "
     "kept in the 0-255 range: the EfficientNet backbone embeds its own rescaling "
     "and normalization layers, so no additional division by 255 is applied, "
     "avoiding a double-normalization error. Training-time augmentation, read "
     "directly from the saved model, comprises horizontal flips, small rotations "
     "(+/-0.08 rad), random zoom and mild random contrast (0.1). We did not run a "
     "dedicated duplicate-detection or split-leakage audit; this is noted as a "
     "limitation. CUB-200-2011 is distributed by Caltech for research use [6]; "
     "the raw images are not redistributed in this repository, which ships only "
     "the derived model and evaluation artifacts."),

    # ==================================================================== IV
    ("h1", "IV", "PROPOSED METHODOLOGY"),
    ("h2", "A", "System Architecture"),
    ("p",
     "Figure 1 shows the end-to-end flow. The Next.js/TypeScript frontend sends "
     "an uploaded image to a Python FastAPI backend, which performs validation "
     "(size, MIME type and magic-byte checks), preprocessing, EfficientNetB0 "
     "inference, class-index mapping and ranking, and optional Grad-CAM. The "
     "identified species then conditions two independent services. The backend "
     "is the only component that performs classification; the Groq and eBird "
     "services are reached through separate, self-contained modules and neither "
     "receives the image for classification."),
    ("fig", "1",
     "End-to-end system architecture (illustrative). The CNN pipeline (top) is "
     "the sole classifier; the dashed region marks optional enrichment services "
     "that are conditioned on the identified species and never classify images.",
     "fig1_system_pipeline.png", True),
    ("runin", "Failure handling.",
     "Each boundary degrades independently. A readiness endpoint reports whether "
     "the model artifact is loaded and returns HTTP 503 rather than a fabricated "
     "prediction when it is not. Groq and eBird failures are classified and "
     "surfaced distinctly (Sections IV-F, IV-G) and never block classification."),

    ("h2", "B", "Model Architecture"),
    ("p",
     "The classifier (Fig. 2) is an EfficientNetB0 backbone [4] pre-trained on "
     "ImageNet [2], followed by global average pooling, a dropout layer with "
     "rate 0.3 [10], and a dense softmax layer with 200 outputs. The saved model "
     "(Keras 3.13 / TensorFlow 2.21 [17]) has 4,305,771 total parameters, of "
     "which 2,293,720 are trainable and 2,012,051 are frozen; the partial "
     "trainable fraction indicates that fine-tuning extended into the upper "
     "backbone rather than the classification head alone. The serialized "
     "artifact is 36.4 MB. The exact set of unfrozen layers and the boundary "
     "between the head-training and fine-tuning phases are not separately "
     "labelled in the artifacts and are marked for verification."),
    ("fig", "2",
     "Model architecture: an ImageNet-pretrained EfficientNetB0 backbone with a "
     "global-average-pooling, dropout (p=0.3) and 200-way softmax head.",
     "fig2_model_arch.png", False),

    ("h2", "C", "Mathematical Formulation"),
    ("p",
     "For an input image x the network produces a logit vector z(x) over K=200 "
     "classes. The softmax transform yields a score vector p whose i-th entry is"),
    ("eq", 1, "eq1.png"),
    ("p",
     "where z_i(x) is the logit for class i. The predicted label is the "
     "arg-max, and the top-k candidates are the k classes with the largest "
     "scores:"),
    ("eq", 2, "eq2.png"),
    ("p",
     "The supervised objective for this single-label softmax classifier is "
     "categorical cross-entropy,"),
    ("eq", 3, "eq3.png"),
    ("p",
     "with y the one-hot target. We note that the exact loss and optimizer used "
     "during training are not recorded in the available artifacts; cross-entropy "
     "is the conventional and near-certain choice for this output layer and is "
     "stated as such rather than asserted from a training log. Crucially, the "
     "entries of p are *uncalibrated* scores, not empirical probabilities, and "
     "we present them accordingly."),

    ("h2", "D", "Training and Preprocessing"),
    ("p",
     "Inputs are 224x224x3 RGB tensors in the 0-255 range (Section III). The "
     "stored training history spans 20 epochs and records train and validation "
     "top-1/top-5 accuracy, loss and the learning rate, which starts at 1e-3 and "
     "decays toward zero under a schedule. A fixed random seed (42) is recorded. "
     "The optimizer identity, batch size, precise learning-rate schedule and the "
     "training hardware are not present in the artifacts, since the Colab "
     "training notebook is not included in the repository; these are reported as "
     "requiring verification rather than inferred. Figure 3 plots the recorded "
     "curves: training top-1 accuracy reaches 0.936 while validation top-1 "
     "plateaus near 0.72, an approximately 21-point gap that indicates "
     "overfitting despite augmentation and dropout."),
    ("fig", "3",
     "Training dynamics over the 20 recorded epochs (from training_history."
     "json). (a) Train/validation top-1 and validation top-5 accuracy; (b) "
     "train/validation cross-entropy loss. The widening train-validation gap is "
     "consistent with overfitting.",
     "fig3_training_curves.png", False),

    ("h2", "E", "Explainability (Grad-CAM)"),
    ("p",
     "Grad-CAM [11] attributes a prediction to spatial regions of the final "
     "convolutional feature map. Let A^k be the k-th feature-map channel of the "
     "backbone's last convolutional block (7x7x1280) and y^c the score for class "
     "c. The channel importance weights and the localisation map are"),
    ("eq", 8, "eq8.png"),
    ("eq", 9, "eq9.png"),
    ("p",
     "where Z is the number of spatial locations and ReLU keeps only positive "
     "contributions. Because the trained model nests the EfficientNetB0 backbone "
     "as a sub-model, the Keras 3 functional graph cannot be re-wired to tap the "
     "inner feature map directly; our implementation instead runs the forward "
     "pass eagerly under a gradient tape that watches the backbone output, then "
     "applies the backbone's remaining head layers. The raw map is validated for "
     "finiteness and a non-zero dynamic range before being normalized to [0,1]; "
     "a degenerate map raises a controlled error and the interface shows an "
     "\"unavailable\" state rather than a blank or misleading overlay. The map is "
     "bilinearly resized to 224x224, colour-mapped, and composited with a "
     "per-pixel alpha so that low-activation regions retain the original image. "
     "We stress that a heatmap indicates where activations influenced the score; "
     "it is an attribution aid, not evidence of causal reasoning or correctness "
     "[11], [12]."),
    ("fig", "6",
     "Grad-CAM example from the training pipeline (gradcam_example.png): the "
     "original image (left) and the class-activation overlay (right). Warm "
     "regions mark the areas whose activations most influenced the predicted "
     "class score.",
     "fig6_gradcam.png", False),

    ("h2", "F", "Species Intelligence (Groq)"),
    ("p",
     "After the CNN produces a label, an optional component queries a "
     "Groq-hosted large language model through its OpenAI-compatible chat API to "
     "generate a structured species summary (overview, habitat, diet, behaviour, "
     "notable facts, conservation note and suggested questions) and to answer "
     "free-form user questions. The configured model is openai/gpt-oss-120b with "
     "openai/gpt-oss-20b as a transient-failure fallback; both were verified "
     "available for the API key. The API key is read only from the backend "
     "environment and is never exposed to the client. Requests use JSON-mode "
     "responses that are schema-validated; failures are classified (rate-limited, "
     "temporarily unavailable, timeout, authentication, quota, configuration) and "
     "transient classes are retried at most twice with exponential backoff and "
     "jitter before the fallback model is tried. The language model is an "
     "enrichment layer only: it does not see the image for classification, and "
     "the classifier is fully functional when the service is unavailable. "
     "Generated text is explicitly labelled as AI-generated and is not an "
     "authoritative biological source; factual verification of model output is a "
     "known limitation."),

    ("h2", "G", "Location-Aware Species Discovery (eBird)"),
    ("p",
     "The discovery component answers \"where can I see this species near me?\" "
     "using the eBird API 2.0 [16]. The predicted species is mapped to an eBird "
     "species code via its human-verified scientific name against the official "
     "eBird taxonomy, never by string-matching a common name; scientific names "
     "are verified for 128 of the 200 classes, and unresolved species are "
     "reported as such rather than guessed. The backend then requests recent "
     "species-specific observations near the supplied coordinates and nearby "
     "hotspots, using the exact coordinates from the request (bounded to a "
     "radius of at most 50 km and a look-back of at most 30 days). Observations "
     "are ranked nearest-first by great-circle distance,"),
    ("eq", 10, "eq10.png"),
    ("p",
     "where r is the Earth radius and (phi, lambda) are latitudes and "
     "longitudes. Every response echoes the search centre, radius and time "
     "window so the interface can display exactly what was queried. An API error "
     "is reported distinctly from a genuine empty result, and browser "
     "geolocation is optional and requested only on explicit user action. We "
     "emphasise that recent reported sightings are community observations, not a "
     "guarantee of current presence, and are distinct from a species' range or "
     "abundance; sensitive-species handling follows eBird's own data policies."),

    # ===================================================================== V
    ("h1", "V", "EXPERIMENTAL SETUP AND EVALUATION"),
    ("p",
     "Evaluation uses the 5,794-image held-out CUB-200-2011 test split (200 "
     "classes). We report top-1 and top-5 accuracy, macro and weighted "
     "precision, recall and F1, per-class F1, the confusion matrix, inference "
     "latency, and model size. For a per-class count TP_c, FP_c and FN_c, "
     "precision, recall and F1 are"),
    ("eq", 4, "eq4.png"),
    ("eq", 6, "eq6.png"),
    ("p",
     "and the macro average is the unweighted mean over the K classes,"),
    ("eq", 7, "eq7.png"),
    ("p",
     "Top-1 accuracy alone is an inadequate summary for fine-grained "
     "classification with near-balanced support: it hides which species are "
     "systematically confused and treats a confident error the same as a "
     "near-miss. Macro-averaged F1 and the confusion matrix expose the per-class "
     "and congeneric structure of the errors, which is the behaviour that most "
     "affects a birdwatching user. All reported test metrics were additionally "
     "recomputed from the stored confusion matrix and agree with the saved "
     "metrics file to four decimal places, confirming class-index integrity "
     "between training and inference."),
    ("runin", "Calibration and OOD.",
     "We did *not* compute a calibration error or an out-of-distribution "
     "detection metric. Consistent with the literature [13], [14], we therefore "
     "make no calibration or robustness claim; the softmax scores are treated as "
     "uncalibrated and the confidence threshold described below is a heuristic."),

    # ==================================================================== VI
    ("h1", "VI", "RESULTS AND DISCUSSION"),
    ("p",
     "Table III reports the headline classification metrics on the held-out test "
     "set. The model attains 71.06% top-1 and 92.44% top-5 accuracy, with a "
     "macro-F1 of 0.715. The closeness of macro and weighted figures reflects "
     "the near-uniform class support."),
    ("table", "III", "CLASSIFICATION METRICS ON THE HELD-OUT TEST SET (5,794 IMAGES, 200 CLASSES)",
     ["Metric", "Value"],
     [
        ["Top-1 accuracy", "71.06%"],
        ["Top-5 accuracy", "92.44%"],
        ["Macro precision", "0.7352"],
        ["Macro recall", "0.7127"],
        ["Macro F1", "0.7146"],
        ["Weighted F1", "0.7127"],
     ], False),
    ("p",
     "The training curves (Fig. 3) and the roughly 21-point gap between training "
     "(0.936) and validation (~0.72) top-1 accuracy indicate overfitting; the "
     "held-out test top-1 (71.06%) is close to the best validation accuracy "
     "(72.37%), so the model generalises to the test split at the validation "
     "level but no better. We report the test figure, never the training or "
     "validation figure, as the headline result."),
    ("runin", "Per-class behaviour.",
     "Figure 5 shows the per-class F1 distribution and the weakest classes. "
     "Per-class F1 ranges from 0.19 to 0.98 (mean 0.715). The strongest classes "
     "are visually distinctive birds (e.g. Pileated Woodpecker 0.98, Horned "
     "Puffin 0.98, White Pelican 0.98), whereas the weakest are members of "
     "visually similar groups (Table V). This spread is the practical reason "
     "top-1 accuracy understates the difficulty for the hardest species."),
    ("fig", "5",
     "Per-class performance on the held-out test set. (a) Distribution of "
     "per-class F1 (mean 0.715); (b) the eight weakest classes, all members of "
     "visually similar groups.",
     "fig5_perclass.png", False),
    ("table", "IV", "BEST- AND WORST-PERFORMING CLASSES BY F1 (HELD-OUT TEST)",
     ["Class", "P", "R", "F1", "n"],
     [
        ["Pileated Woodpecker", "0.97", "1.00", "0.98", "30"],
        ["Horned Puffin", "1.00", "0.97", "0.98", "30"],
        ["White Pelican", "0.95", "1.00", "0.98", "20"],
        ["Rose-breasted Grosbeak", "0.97", "0.97", "0.97", "30"],
        ["Least Flycatcher", "0.21", "0.48", "0.29", "29"],
        ["Herring Gull", "0.39", "0.23", "0.29", "30"],
        ["Western Wood-Pewee", "0.40", "0.20", "0.27", "30"],
        ["California Gull", "0.38", "0.20", "0.26", "30"],
        ["Chipping Sparrow", "0.19", "0.20", "0.19", "30"],
     ], False),
    ("runin", "Confusion structure.",
     "Figure 4 shows the row-normalized 200x200 confusion matrix; off-diagonal "
     "mass concentrates in small clusters of congeneric species. Table V lists "
     "the most frequent confusions, which are dominated by sparrows, gulls, "
     "terns, grebes, flycatchers, crows/ravens and cormorants - groups that "
     "experienced human observers also find difficult. These are genuine "
     "fine-grained errors rather than arbitrary mistakes."),
    ("fig", "4",
     "Row-normalized confusion matrix over all 200 classes (from "
     "confusion_matrix.npy). A strong diagonal with sparse congeneric "
     "off-diagonal clusters is visible.",
     "fig4_confusion.png", False),
    ("table", "V", "MOST FREQUENT TEST-SET CONFUSIONS (TRUE -> PREDICTED)",
     ["True species", "Predicted species", "Count"],
     [
        ["Chipping Sparrow", "Tree Sparrow", "15"],
        ["Vesper Sparrow", "Savannah Sparrow", "12"],
        ["Eared Grebe", "Horned Grebe", "12"],
        ["Caspian Tern", "Elegant Tern", "12"],
        ["Acadian Flycatcher", "Least Flycatcher", "11"],
        ["Common Raven", "American Crow", "10"],
        ["California Gull", "Western Gull", "10"],
        ["Pelagic Cormorant", "Brandt Cormorant", "10"],
     ], False),
    ("runin", "Computational characteristics.",
     "Table VI reports model size and latency. The stored evaluation recorded a "
     "mean single-image inference latency of 293 ms (p95 313 ms) on a GPU, as "
     "noted in the metrics artifact. On a CPU-only backend we observed a warm "
     "latency of roughly 130-290 ms per image and a one-off cold cost of several "
     "seconds on the first call due to graph tracing. Latency is therefore "
     "environment-dependent and we report both conditions."),
    ("table", "VI", "COMPUTATIONAL CHARACTERISTICS",
     ["Property", "Value"],
     [
        ["Total parameters", "4,305,771"],
        ["Trainable / frozen", "2,293,720 / 2,012,051"],
        ["Serialized artifact size", "36.4 MB"],
        ["Input resolution", "224 x 224 x 3"],
        ["Latency (GPU, stored eval)", "mean 293 ms, p95 313 ms"],
        ["Latency (CPU, warm / cold)", "~130-290 ms / several s"],
     ], False),
    ("runin", "Out-of-distribution behaviour.",
     "Because the softmax ranges over exactly 200 classes, the model cannot "
     "natively signal \"not a supported species\". Feeding clearly out-of-"
     "distribution inputs confirms this: uniform-noise and flat-grey images both "
     "produced low top scores (0.12 and 0.01) that fall below the system's "
     "heuristic abstention threshold (0.35) and are flagged as uncertain. This "
     "threshold reduces confident nonsense but is not a validated out-of-"
     "distribution detector [14]; genuinely unsupported species can still be "
     "mapped to the nearest known class with moderate confidence."),
    ("runin", "Functional verification of integrations.",
     "Table VII records the verification status of each component. Classification, "
     "Grad-CAM, the Groq enrichment and the eBird discovery service were "
     "exercised end-to-end; the backend test suite comprises 58 passing tests "
     "with external services mocked. We did not perform load testing, security "
     "penetration testing or any independent field validation of predictions."),
    ("table", "VII", "FUNCTIONAL VERIFICATION OF SYSTEM COMPONENTS",
     ["Component", "Status", "Evidence"],
     [
        ["CNN classification", "Verified", "Live inference; metrics recomputed"],
        ["Class-index mapping", "Verified", "Startup guard + test"],
        ["Grad-CAM", "Verified", "Live overlay; validation tests"],
        ["Groq enrichment", "Verified", "Live 200 OK; 120b model"],
        ["eBird discovery", "Verified", "Live species-specific sightings"],
        ["Automated tests", "Verified", "58 backend tests pass"],
        ["Field validation", "Not done", "Out of scope"],
     ], False),
    ("runin", "Benchmark versus real-world performance.",
     "All figures above are on curated CUB-200-2011 images. Real user uploads "
     "differ in framing, occlusion, background and image quality, and include "
     "species outside the 200 trained classes, so field accuracy is expected to "
     "be lower than the reported benchmark. We also observed that the external "
     "language-model service can be transiently rate-limited, in which case "
     "enrichment is withheld rather than fabricated. Previously reported "
     "qualitative screenshot cases (a sparrow-like, an eagle-like and a stork/"
     "crane-like bird) could not be re-evaluated here because the original image "
     "files are not present in the repository; they are noted as pending "
     "qualitative case studies and are not used as evidence.",),

    # =================================================================== VII
    ("h1", "VII", "LIMITATIONS AND FUTURE WORK"),
    ("ulist", [
        "*Dataset coverage and shift.* The model knows only 200 largely North-"
        "American species; inputs outside this set are necessarily misclassified, "
        "and curated-benchmark accuracy overstates field performance.",
        "*Fine-grained confusion.* Congeneric species (sparrows, gulls, terns, "
        "grebes, flycatchers) drive most errors and pull per-class F1 as low as "
        "0.19.",
        "*Uncalibrated confidence.* Softmax scores are not calibrated and no "
        "calibration error was measured; the confidence threshold is heuristic.",
        "*No OOD rejection.* There is no validated out-of-distribution detector; "
        "unsupported species can be mapped to the nearest class.",
        "*Explainability scope.* Grad-CAM localises influence but does not verify "
        "correctness, and was not quantitatively validated against annotations.",
        "*External-service dependence.* Groq and eBird are subject to "
        "availability, rate limits and upstream data freshness; sightings are "
        "community reports, not guaranteed presence.",
        "*Provenance gaps.* The training notebook and raw images are absent, so "
        "optimizer, batch size, exact schedule, split methodology and leakage "
        "status remain unverified.",
        "*No field validation.* Predictions were not validated against "
        "expert-confirmed field observations.",
    ]),
    ("p",
     "Future work follows directly from these limitations and is *not* claimed as "
     "implemented: measuring and correcting calibration [13]; adding a validated "
     "out-of-distribution rejection mechanism [14]; stronger, quantitatively "
     "evaluated explainability [12]; a documented leakage and duplicate audit of "
     "the splits; broader taxonomic and geographic coverage; and an independent, "
     "expert-verified field evaluation of real user uploads."),

    # ================================================================== VIII
    ("h1", "VIII", "CONCLUSION"),
    ("p",
     "We presented BirdVision AI, an explainable transfer-learning system for "
     "fine-grained bird species recognition with location-aware species "
     "discovery. A single EfficientNetB0 classifier, transfer-learned on "
     "CUB-200-2011, attains a verified held-out top-1 accuracy of 71.06% and a "
     "macro-F1 of 0.715, with errors concentrated among congeneric species, as "
     "an honest per-class and confusion analysis makes explicit. Around this "
     "classifier the system adds production Grad-CAM attribution and two strictly "
     "separated, fail-safe enrichment services - a Groq language model for "
     "species intelligence and the eBird API for species-specific nearby "
     "observations - without ever delegating classification to them. We have "
     "been deliberate about what is not claimed: the scores are uncalibrated, "
     "there is no out-of-distribution rejection, several training details remain "
     "unverified, and no independent field validation was performed. The result "
     "is a reproducible, defensible reference implementation of an explainable, "
     "context-rich bird-recognition system rather than a production-ready or "
     "scientifically validated identification tool."),

    ("codeavail",
     "The implementation (backend, frontend, evaluation artifacts and the "
     "scripts that regenerate this paper's figures) resides in the project "
     "repository. No public repository URL is asserted here; the code is "
     "available from the authors on request, subject to the dataset's research-"
     "use terms."),
]

REFERENCES = [
    "Y. LeCun, Y. Bengio and G. Hinton, \"Deep learning,\" Nature, vol. 521, "
    "no. 7553, pp. 436-444, 2015.",
    "J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li and L. Fei-Fei, \"ImageNet: "
    "A large-scale hierarchical image database,\" in Proc. IEEE CVPR, 2009, "
    "pp. 248-255.",
    "K. He, X. Zhang, S. Ren and J. Sun, \"Deep residual learning for image "
    "recognition,\" in Proc. IEEE CVPR, 2016, pp. 770-778.",
    "M. Tan and Q. V. Le, \"EfficientNet: Rethinking model scaling for "
    "convolutional neural networks,\" in Proc. ICML, 2019, pp. 6105-6114.",
    "K. Simonyan and A. Zisserman, \"Very deep convolutional networks for "
    "large-scale image recognition,\" in Proc. ICLR, 2015.",
    "C. Wah, S. Branson, P. Welinder, P. Perona and S. Belongie, \"The "
    "Caltech-UCSD Birds-200-2011 dataset,\" California Inst. Technol., Tech. "
    "Rep. CNS-TR-2011-001, 2011.",
    "G. Van Horn et al., \"The iNaturalist species classification and detection "
    "dataset,\" in Proc. IEEE CVPR, 2018, pp. 8769-8778.",
    "T.-Y. Lin, A. RoyChowdhury and S. Maji, \"Bilinear CNN models for "
    "fine-grained visual recognition,\" in Proc. IEEE ICCV, 2015, pp. 1449-1457.",
    "J. Yosinski, J. Clune, Y. Bengio and H. Lipson, \"How transferable are "
    "features in deep neural networks?,\" in Proc. NeurIPS, 2014, pp. 3320-3328.",
    "N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever and R. "
    "Salakhutdinov, \"Dropout: A simple way to prevent neural networks from "
    "overfitting,\" J. Mach. Learn. Res., vol. 15, no. 1, pp. 1929-1958, 2014.",
    "R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh and D. "
    "Batra, \"Grad-CAM: Visual explanations from deep networks via "
    "gradient-based localization,\" in Proc. IEEE ICCV, 2017, pp. 618-626.",
    "A. Chattopadhay, A. Sarkar, P. Howlader and V. N. Balasubramanian, "
    "\"Grad-CAM++: Generalized gradient-based visual explanations for deep "
    "convolutional networks,\" in Proc. IEEE WACV, 2018, pp. 839-847.",
    "C. Guo, G. Pleiss, Y. Sun and K. Q. Weinberger, \"On calibration of "
    "modern neural networks,\" in Proc. ICML, 2017, pp. 1321-1330.",
    "D. Hendrycks and K. Gimpel, \"A baseline for detecting misclassified and "
    "out-of-distribution examples in neural networks,\" in Proc. ICLR, 2017.",
    "S. Kahl, C. M. Wood, M. Eibl and H. Klinck, \"BirdNET: A deep learning "
    "solution for avian diversity monitoring,\" Ecol. Informatics, vol. 61, "
    "art. 101236, 2021.",
    "B. L. Sullivan, C. L. Wood, M. J. Iliff, R. E. Bonney, D. Fink and S. "
    "Kelling, \"eBird: A citizen-based bird observation network in the "
    "biological sciences,\" Biol. Conservation, vol. 142, no. 10, pp. "
    "2282-2292, 2009.",
    "M. Abadi et al., \"TensorFlow: A system for large-scale machine "
    "learning,\" in Proc. USENIX OSDI, 2016, pp. 265-283.",
    "M. S. Norouzzadeh et al., \"Automatically identifying, counting, and "
    "describing wild animals in camera-trap images with deep learning,\" Proc. "
    "Nat. Acad. Sci. USA, vol. 115, no. 25, pp. E5716-E5725, 2018.",
]

# Equations as LaTeX (for mathtext rendering and the .tex file)
EQUATIONS = {
    1: r"p_i = \frac{e^{z_i(x)}}{\sum_{j=1}^{K} e^{z_j(x)}}",
    2: r"\hat{y} = \mathrm{arg\,max}_{i}\; p_i, \quad \mathcal{T}_k = \mathrm{argsort}(p)",
    3: r"\mathcal{L} = -\sum_{c=1}^{K} y_c \, \log p_c",
    4: r"P_c = \frac{TP_c}{TP_c + FP_c}, \quad R_c = \frac{TP_c}{TP_c + FN_c}",
    6: r"F1_c = \frac{2\,P_c\,R_c}{P_c + R_c}",
    7: r"F1_{\mathrm{macro}} = \frac{1}{K}\sum_{c=1}^{K} F1_c",
    8: r"\alpha_k^{c} = \frac{1}{Z}\sum_{i}\sum_{j}\frac{\partial y^{c}}{\partial A_{ij}^{k}}",
    9: r"L^{c} = \mathrm{ReLU}\left(\sum_{k}\alpha_k^{c}\, A^{k}\right)",
    10: r"d = 2r\,\mathrm{arcsin}\sqrt{\sin^{2}\frac{\Delta\phi}{2} + \cos\phi_1\cos\phi_2\sin^{2}\frac{\Delta\lambda}{2}}",
}
