# Baseline Checksums — Prachuap Khiri Khan v1.0.0
**Repository:** s0815547799-lab/rainfall-trend-analysis  
**Branch:** claude/hydroclimatology-claude-md-kudre  
**Release:** v1.0.0  
**Generated:** 2026-05-29  
**Total tracked files:** 671  
**Total categories:** 10  
**Hash algorithm:** SHA-256  

> These checksums constitute the definitive integrity record for the v1.0.0 release.  
> Any deviation from these hashes in reproduced files indicates a change to the scientific pipeline.  
> Figure checksums are also stored in `results/archive_figures/checksums.sha256`.

---

## Configuration and Root Files

| SHA-256 | File Path |
|---|---|
| `ba16bff091f2e1966e012c2da12839a140f18225b719742d778d8de959a0a685` | `.gitignore` |
| `800fbacde301eba49a9306b7bc92b13b09b4d565329cee4adc0aa244c8f9d678` | `LICENSE` |
| `23ed1095c5c04825e5687d034ada413dfb6589b3573460ad07f807d27b241527` | `README.md` |
| `2d30be8201775348140ffd9e507ef6a384d3968b6323b534a8491379bf04f179` | `requirements.txt` |
| `cafcff2f6baabb3086211d6ff62858f63ca782998a267e4ae43cbda1e74276d8` | `CLAUDE.md` |
| `f047fa57d3fe3491a6f2312494cb40bafda5d6b98aefc1617a134633fbd72300` | `CHANGELOG.md` |

---

## Input Data Files

| SHA-256 | File Path |
|---|---|
| `f845a0248d3a2008e1d239fe04f63043f023445d077d5ee2c63e86203f498457` | `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` |
| `6946733e4e13ea3011a21614cdef4b2bed398fcc52f405bc615b70f80f0fb444` | `rainfall_data.csv` |
| `051cf72a5e547d480a79186145ebb4e8ab02bc227f26a6e71db899c3e46ecf3e` | `station_coordinates.csv` |
| `8f9b5759bd45cb621933f97e2cb7b222eab99d8af8ca1dca4733860ec34073f8` | `data/stations.csv` |

### Shapefiles (Primary Basin Boundary — Prachuap Province)

| SHA-256 | File Path |
|---|---|
| `656a73846acf8a58d9e1b853da2f71c3101e3698095646b55aca1af09fe818bc` | `30_amarea_prachuap_khiri_khan.dbf` |
| `a2d5afe2671da3db01038e8dc16449da6e3fa505104d09492a7c101f34f87cac` | `30_amarea_prachuap_khiri_khan.prj` |
| `bc447273df1150027397fca0dd788f3e0b6c1c698ce5ec4b0ee6b120cddbd17b` | `30_amarea_prachuap_khiri_khan.shp` |
| `875b71e0350bf5765b3abbbe59f312bb1b42035f6ae0082755b72c2636760c57` | `30_amarea_prachuap_khiri_khan.shx` |

### Shapefiles (Current Boundary — v5 Pipeline)

| SHA-256 | File Path |
|---|---|
| `1c6fb42d81c14d641f7e4dc9b733e31c8c1989f65038a43df515fc3c56020066` | `boundaries/current_boundary/boundary.dbf` |
| `c77be1866509aabe2a1252f1985cf6edf712ac78fb01f3cc0a0c6a5a82e2f250` | `boundaries/current_boundary/boundary.prj` |
| `bff58ae14f4a8c298fb84128df4b882d69e44fb58142c7953bdf7ac704892b89` | `boundaries/current_boundary/boundary.shp` |
| `3b5a95ebf1da11c4fb4377d77a6290eba3302079e098b77e04ed113d0e8f4d54` | `boundaries/current_boundary/boundary.shx` |

---

## Python Scripts — Top-Level

| SHA-256 | File Path |
|---|---|
| `f84bea9d8d7cf2ff36074e86e0aac656723b4094e4522df60a2b47e8667eb79f` | `rainfall_trend_analysis_v3.py` |
| `ac8fa10b666c56df1aeeadaf956e4cf5ee94c0e2ecfea50c48587d8eec37fc25` | `rainfall_trend_analysis_v4.py` |
| `0d27d82c6631beaeaff44ecf18f3d90a372a97788d593acb30dee6d952798a77` | `rainfall_trend_analysis_v5.py` |
| `1a884483cadd37c2018294a7c28b4701f05d39b9123a4d0d41a2f0e93a958e1f` | `generate_all_vs_mk_workbook.py` |
| `30cf42c6b5cea641f12aa060530f593187eb8dd7df2db0db430ea350a7bb10d7` | `generate_final_validation.py` |
| `d3fb04ff8676a7f655fa624ad416b46f968d9dfd625477873859779cced01348` | `generate_q1_maps.py` |
| `0974f1f36eee3cae05b8a3b5631f522799c25afb92cd5b4164ff076dc9b20ce9` | `generate_reviewer_summary.py` |
| `ef55cac222ab43b1ece3d5c66e1b109951db63fc56a72e95275944910bb910e9` | `generate_tfpw_audit.py` |
| `c247d7d2c453cec2d24eacaa7c626b558914370a27c78fea38d88d4aedfb9496` | `generate_trend_comparison.py` |
| `133ac1150c072052ae1c7900d25b47148fa40663a4d89729fcf86866bcc635da` | `generate_trend_comparison_analysis.py` |
| `9bce72baf971bbc6ce28366329438406d911098b81f8e14cf401872d3e7d998b` | `Comparative_4MMK.py` |
| `00c59d75273bc79aa499adc25f65fc30dd6b9a5623e3e9ad009e7824a52f92ec` | `calval_split.py` |

---

## Python Package — rta/

| SHA-256 | File Path |
|---|---|
| `77cd1cd48bf2be499d09d78e1fd7c5073b69bfd3d7d89bada2a0b6c456ed6ab3` | `rta/__init__.py` |
| `7f4d0b6afe6a1e25130a1cb11ef1a0a9a6512fcb326900785c62a60969ceafc0` | `rta/aggregation.py` |
| `495f4b4d3ede79f7478cfb900ddca0e8a501096fc228cbc97e032b11281db26e` | `rta/autocorr.py` |
| `6b9a7d80cd383502aeb6e23ac67d3778a2bdc06c7ee9afa55e9ed284edf6e1c5` | `rta/batch.py` |
| `27310261d8c7fea0cfb88f67ae3111587b4ad4dd9a25a285cec547bd1c5db9f6` | `rta/checkpoint.py` |
| `72c4f29296dea7939ee7d2bfd5e04a7eff2872e0705f053e0b14ea45f6ca709d` | `rta/config.py` |
| `69dbbc5f3c3de3d7741d78052917c43d98cd493aa5bebd8d5b8f3eddcc7460a6` | `rta/excel_output.py` |
| `defdd27f9458e27f8b9dc7ecd0c16f3520c520585c841eed5dd662e0c71ab177` | `rta/field_sig.py` |
| `358a66b97b26bfd0821f69b658fce51ce7e723f52e4fdebddab0fb1f846f922e` | `rta/field_significance.py` |
| `05c4cf8eafcf9febf24406c15ee1d28ca0eddfb133a2348db6226ea35cec2533` | `rta/io.py` |
| `9a3a5bffdc9a349da17f6519ad1ae4259bf60c4be7878411a34ab59fc60c4b9e` | `rta/markdown.py` |
| `32a55336efe907a86adbca70cfab55e007f11dcd40e9bdf8ac68c858ee782a2d` | `rta/pw.py` |
| `072ea127ff179d3fa573cae5748e2a3e2d4d88786571b80d9ac0dc37a0c1aecc` | `rta/spatial.py` |
| `d7d30c1febd3bb507ef8a2baf440379818d45828059331ec946e9e958ec42fb8` | `rta/spatial_maps.py` |
| `4de719ed374ba3ed960878f624cced51fee425a181346fc757346a2ff0ff63f7` | `rta/tfpw.py` |
| `10eacc1316143c1c9189e406182e3d7b4ec8817fe3d91c682bf50b13d1cf2dec` | `rta/trend_comparison_analysis.py` |
| `73f036eb2a4e28f06c4d91cb98000c98a2482c550b88ab52d7a9e9dceb7c8bad` | `rta/trend_method_comparison.py` |
| `f1d9bfbe710df1d9b587cb29b35ae5ff35880cad4db6843824e51ff7d635616a` | `rta/trend_tests.py` |

### rta/figures/ Subpackage

| SHA-256 | File Path |
|---|---|
| `7a8bb7297edae13e847bdc9503229a70e3fa2c897fc1c45bd1e9c5c5572ed87d` | `rta/figures/__init__.py` |
| `b7e72f56f227d8bf5b7cf82b112bf59b354e12eee96cfeda5aa4915468dfdfa3` | `rta/figures/acf_plots.py` |
| `0f3dd864909d75982aa06c41b661c8be576ec51435b6643577f8e6eff07b532d` | `rta/figures/bars.py` |
| `04ab6a8f7c986b715fb2e8b8a80ba51ad3a934edfcbd6d7b0d8ce6bd64ccbe2b` | `rta/figures/climatology.py` |
| `274c72b8bc760257af585feaa9ef40cb29fcaee3c0959052f19209999fc9bbc7` | `rta/figures/comparison.py` |
| `fa3c770ee5ee9f0e955249f59c83d0195d9b195b1abe950167112a863f523f44` | `rta/figures/field_sig_plot.py` |
| `543cc58882a1f452f1a61f17902595b314dfa67b041d5a9162f59fe209c8804b` | `rta/figures/heatmaps.py` |
| `58a6498249edb20b769e24548084b6d8ef6a9c8e9e6cd5af37b83a8821042e31` | `rta/figures/helpers.py` |
| `3bdc178a3d24403b85b02522b750998f7ed6796a65d6feb3cbb7f9246eead05b` | `rta/figures/method_comparison.py` |
| `eec9b074ead5b07f378c4e36d656b4deaeb6c119b346cdf96921a7eb0cbd82f3` | `rta/figures/spatial.py` |
| `67da6d757d4d910a0c333e5799de945599dc7a3da612464b4ac3628f66edfe39` | `rta/figures/spatial_maps.py` |
| `2213416424869ffa394815026b79dacdd1cae427d99b888ff886f0f027a81654` | `rta/figures/taylor.py` |
| `6e620814aea4b84c36b6dc0091109f8025df1351e88543b4514acca557e6e591` | `rta/figures/timeseries.py` |

---

## Python Package — rta_v5/

| SHA-256 | File Path |
|---|---|
| `878ecacfb5ddd3e7404bc5ad265635688210dcd966ae8c7e9cc63b7bd91dcd74` | `rta_v5/__init__.py` |
| `10e9fbc500f23c34a10598966385bda45754838f54e1d0d19d4437f8f95fb887` | `rta_v5/spatial_export_v5.py` |
| `f46db6607e3828307c100b4d0563bc359507bb36a65d4e53002238d3630ed394` | `rta_v5/spatial_interpolation_v5.py` |
| `6e314e77b88620195e263687fc2d6d4008326ecff2da0aa73f0c7bf4a89de2d1` | `rta_v5/spatial_layout_v5.py` |
| `10a185a582787b6cd6e8e63d7c3ace3f688e80c6ad2696e56653a9f60bcd274c` | `rta_v5/spatial_publication_q1_v5.py` |
| `99a4ce06a626526447c401f12b42a0eb8dae7ce66d559c82a17a4b69d0c87261` | `rta_v5/spatial_validation_v5.py` |

---

## Documentation — Root Level

| SHA-256 | File Path |
|---|---|
| `cafcff2f6baabb3086211d6ff62858f63ca782998a267e4ae43cbda1e74276d8` | `CLAUDE.md` |
| `f047fa57d3fe3491a6f2312494cb40bafda5d6b98aefc1617a134633fbd72300` | `CHANGELOG.md` |
| `2ec1dd3d0cda10bc462d4e5b6b1bd9bbc95088888fb0a3a66771cc66bc94953b` | `CONFIGURATION_GUIDE.md` |
| `91e94edd47e57f514258341b398385e2492b622e0cecc6bcad4ebffd00492a7c` | `DATA_DICTIONARY.md` |
| `cdbdd044c233a427ebfc5890268ac258e5c01ae4def05fbe7e12ed7c5cbe7ee7` | `DISCUSSION_TEMPLATE_VALIDATION.md` |
| `c8d21aacccb289a2fa5489b9e536604619d7f3dab30ca0788f4afbfbf4a8ed57` | `FIGURE_INVENTORY.md` |
| `17de6d6dca29e714c523ae103c3db551af4179317ff5179f0cb601f862a3ee9d` | `FIGURE_QA_REPORT.md` |
| `1f1318af2881ea9658423e1dbdd74a2b406b9fe491410c2d55e263e387f159da` | `FIGURE_TABLE_CROSSREF.md` |
| `2ecd732a0261ece6836298712ffe92c4f9e7c52c7ae74ee2c7b44c34b216bfcf` | `FINAL_RELEASE_AUDIT.md` |
| `57d60496da55f37369cb8064ae92c2a5d67ed49eaf25ae4bfa469d95c564a097` | `FINAL_RELEASE_SUMMARY.md` |
| `6e98393adfd8576b7b08960d2fbf1f3b671f828556478ed0f6c89221d2aaa5ec` | `FRAMEWORK_CONVERSION_REPORT.md` |
| `830e8d62dc632ced1a65b742b0949c2ca9149a8baa64f387ede5014846583755` | `INSTALLATION_GUIDE.md` |
| `2aa1ab647fd0b4885e37355e1f487a2c83cae7a5e5b0f2083c2682d8b6e7fad6` | `MANUSCRIPT_PACKAGE_CHECKLIST.md` |
| `467be7fd6eeb69815a6050cc018038e16c8fa69fd847831ee22a71d1d8bcdd7c` | `MANUSCRIPT_READINESS_AUDIT.md` |
| `16ecb3d9ab11462c6076b51a5407e2770cdd85b3ee139bea4a70b704e73b57e2` | `PIPELINE_VALIDATION_REPORT.md` |
| `1c5b35ed3ab5d01013df030b1aa22132ffee0ae955e6d161ce74a0e5a96a6423` | `PROVINCE_SETUP_GUIDE.md` |
| `23ed1095c5c04825e5687d034ada413dfb6589b3573460ad07f807d27b241527` | `README.md` |
| `d1d8bb6d17cb92778d8a387c40b69bd3990dd8ebd891c0aa26dc1623f1420466` | `RELEASE_CERTIFICATION_v1.0.md` |
| `cf6c172d3cbc22c633427d2ee94c3efeb97feeb38f5f01a6b64239c5e86aeb6e` | `RELEASE_INVENTORY.md` |
| `15a0c7afe440c25e4ac8a68a5c8e168b5167a0ed4e50aff955db10ab2a0f5728` | `RELEASE_MANIFEST.md` |
| `33097c8063e9b41deecfec8ae9cd65520badae6329bed676dc6d729ee6751747` | `RELEASE_READINESS_REPORT.md` |
| `5d9a315052e8a386263410a823b6abde5a5a8a9228b322d8921ba797aa3ae1bf` | `RELEASE_v1.0/README.md` |
| `0f0fc0aed97b5ca2b5df6088b2a53555d737b6828c75ddd88ad24b614ff2a5cc` | `REPRODUCIBILITY_AUDIT.md` |
| `695d31029150347e2b0d33c71c73e46121ab6b1aa4fc5c5085b356677da26fa9` | `REPRODUCIBILITY_CERTIFICATION.md` |
| `9efb495b5ef5a6fe14ce12ab41ef2bc8d21e48a0d69f344e72d3d4781b448742` | `REPRODUCIBILITY_FINAL_CHECK.md` |
| `33bd6de8b290f8285bf0d601af2a409086f1f28a61bed54390988ce62f6419cc` | `TECHNICAL_DEBT_REGISTER.md` |
| `96a8c0905db40fc53520b014fc55dc008eae11bf95a2d880ea344aa465f66104` | `USER_GUIDE.md` |

---

## Documentation — Results Directory

| SHA-256 | File Path |
|---|---|
| `ad861a4b315f3f574880113deae32e373551399bea9de1b7d7fab1ad9d6268d1` | `results/Workbook_Inventory_Report.md` |
| `d229a86192e775f9658f2ab42592d5da5ce9fa719ff52fac6575b06701df0a69` | `results/archive_figures/FIGURE_ARCHIVE_REPORT.md` |
| `feb0ca1e455ad2d01c51a7e66d3233810614fcca92fb89ebdba8b14b1b13d80e` | `results/final_N33/manuscript_tables/Output_TrendV4_Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan_Research_Summary.md` |
| `49d893ad3ab0ed00d9b5bdf75530e1808ad0207cae70d4f8e19aab0083086eef` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Comparisons/MMK_vs_MK_Summary.md` |
| `91b21927bad5adf0f93fc105ece4f118598c30a0f1b9b83e9e9bc9801b2a74da` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Comparisons/PW_vs_MK_Summary.md` |
| `2858cdc8184bcb21cc0d074eddba8ecd4b818f857102f587dbfe182c50feecca` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Comparisons/TFPW_vs_MK_Summary.md` |
| `98d07b2ba6e7b5d2d8f838211b761c58a7bea3d780e754ed17782cfff9517678` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Methods/MK_Results_Summary.md` |
| `0a0c813978a25bfec83de4690b68fe8b98797d62c5211c86d4879058f0c7f545` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Methods/MMK_Results_Summary.md` |
| `d4f2c0260a9cf376e4c994728605cb0902d2758cd7cf57b91daff042afd421ac` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Methods/PW_Results_Summary.md` |
| `9db6a9342401bc29fb26e8a904bc44cd8b7c7e23870b5f6c5a65dd15997f477b` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Methods/TFPW_Results_Summary.md` |
| `e5d47142300930b3f23fdfb31a07c253ae641e7140bb54ca0b38387fa6e82b2b` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/Discussion_Template.md` |
| `85cbaf2dd22fc71d5b6ceaa7edbe622b803c71cac86b25faa118f311724e65f1` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/Results_Template.md` |
| `830c7153b2ab1889bf81c4d6c9287a44946fb47617a7599686e15fbbb31a8283` | `results/final_N33_v5/manuscript/Boundary_Config_v5.md` |
| `428210280f09f63d38278ad01a1259c45300054386421bec4fa1bdec064c6051` | `results/final_N33_v5/manuscript/Spatial_Methods_Q1_v5.md` |

---

## Excel Workbooks

| SHA-256 | File Path |
|---|---|
| `99067aa502bf97c7a71d666cae7e76db21196fc0e2ce3eaf9a2553dac2cee711` | `results/Workbook_Inventory_Report.xlsx` |
| `8f7e08663de735114fd7fe2b5004c9f9bd83b4516b2f85c6459fe6203cfac708` | `results/final_N33/excel/Output_TrendV4_Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan_Results.xlsx` |
| `b04868f7226ef5e9af92d1d3abfd4beae72ffa047226670114edc381e81996a4` | `results/final_N33_v5/Trend_Method_Comparison/Excel/MK_Analysis/MK_Analysis.xlsx` |
| `3f46718367895b0654058aff0effa8f8e2d1092aa67454618da0c2723d722110` | `results/final_N33_v5/Trend_Method_Comparison/Excel/MMK_Analysis/MMK_Analysis.xlsx` |
| `af84dd0d09c96eae0b78311ff77b5425f6d1747876799efcded94b322bd0a482` | `results/final_N33_v5/Trend_Method_Comparison/Excel/MMK_Analysis/MMK_vs_MK_Comparison.xlsx` |
| `e8baaa31e8b0d4494518f244812cde6a59e1169549076c9a4c2dbbf2eba2518b` | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Disagreement_Stations.xlsx` |
| `7a6bec24f29543e143a6566b275d5c4a9b21440d8464107a60ff7c5dc07a07bd` | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Final_Methodological_Assessment.xlsx` |
| `3c9cfb7ae5ab6d6046628bc889abb3fec0b7bd2aeb6b641f84a6b40704a0986b` | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Reviewer_Summary.xlsx` |
| `7bc3165430a02dc88ec33d330b491a9ac821f916f14e26b5fe63fe58914ac2c7` | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/SenSlope_Comparison.xlsx` |
| `3451378c4ae8c48eb1a9d2a459890bc0efe2642259842733f6d81a730e7f3090` | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/TFPW_Audit.xlsx` |
| `15298ebf31bcf1a7cd0bdfcae9249e767882a919a880acf8fddeb3944825c600` | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Trend_Method_Comparison_All_vs_MK.xlsx` |
| `8a3c32a83ce79d4afc6d06b2619d4d1bd77e489d92f191715c4904fba94312db` | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Trend_Method_Comparison_Master.xlsx` |
| `8218d5c8ab6bb17520c1e89360f275bdd87fba2e7528da3a55c81abd33726c17` | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Trend_Method_Comparison_Tables.xlsx` |
| `59fe05e945db00c50bf0c80414bb5eed0e153f72fc5fe6a379a7fbbd065475d8` | `results/final_N33_v5/Trend_Method_Comparison/Excel/PW_MK_Analysis/PW_MK_Analysis.xlsx` |
| `a1469e027a9d638c35002dd889589393a96d4c07924c4a0694f13464502beaab` | `results/final_N33_v5/Trend_Method_Comparison/Excel/PW_MK_Analysis/PW_MK_vs_MK_Comparison.xlsx` |
| `4e37f54f8d4c1804e7baecbd97ffb6e211eea645c6df2d0f37f93669cfcae9b8` | `results/final_N33_v5/Trend_Method_Comparison/Excel/TFPW_MK_Analysis/TFPW_MK_Analysis.xlsx` |
| `910a13755a53207e961763b9dd61757c9d63dfea38335b3bebe817d090375226` | `results/final_N33_v5/Trend_Method_Comparison/Excel/TFPW_MK_Analysis/TFPW_MK_vs_MK_Comparison.xlsx` |
| `5f487b9ccd133e1ca70fcddc4addd1c67aa4bcb6f2c12faf4c58c0300d247c80` | `results/final_N33_v5/Trend_Method_Comparison_Q1.xlsx` |
| `f485ae55cad43a2b2169d965e58717b121fb22cd79025c41e25700999ca41190` | `results/final_N33_v5/validation/Interpolation_Comparison.xlsx` |
| `5c279c420ced37b41ff9a5217b9df60e808e21774a3d8d331d72b7e287402ca1` | `results/final_N33_v5/validation/LOOCV.xlsx` |

### Manuscript Tables (CSV + XLSX pairs)

| SHA-256 | File Path |
|---|---|
| *(see git ls-files for CSV hashes)* | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M1_Method_Agreement.csv` |
| `4b5770c40ac06b1762e6fbed9d53ec10aa9e1aac56be8abe69b48901d474ef49` | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M1_Method_Agreement.xlsx` |
| *(see git ls-files for CSV hashes)* | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M2_Significance_Transitions.csv` |
| `ef5707b9d0d634fb06c64f02da67aeb065114276d48e658b890ea2da43e77021` | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M2_Significance_Transitions.xlsx` |
| *(see git ls-files for CSV hashes)* | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M3_Correction_Factor_Impact.csv` |
| `2763141b00e10ba89f502a368af2c5ffb356136d171aa399f7dfaa1ce09f8771` | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M3_Correction_Factor_Impact.xlsx` |
| *(see git ls-files for CSV hashes)* | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M4_Station_Disagreement_Inventory.csv` |
| `d16a354daad0907bb88b5c2a57e3187797633edfe0d2ee5dd44cb3f8edb4fa2a` | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M4_Station_Disagreement_Inventory.xlsx` |
| *(see git ls-files for CSV hashes)* | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M5_Field_Significance_Comparison.csv` |
| `82367a8ff7bd29533f7b32064d3c67cc14e1411098101d23487c560cf7e038cb` | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M5_Field_Significance_Comparison.xlsx` |
| *(see git ls-files for CSV hashes)* | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M6_Top_AC_Affected_Stations.csv` |
| `64098ffe4cf7d1f499f7ab9eb799765928cf13fbfadf59cd76b1a839e2588e1d` | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M6_Top_AC_Affected_Stations.xlsx` |
| *(see git ls-files for CSV hashes)* | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M7_Method_Ranking_Summary.csv` |
| `9742a8799e9ea067f2e92c7e0535f20c4f8cb53db4d194b9b9c7deaa255bd1bc` | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M7_Method_Ranking_Summary.xlsx` |

---

## Archived Figures — Primary Pipeline (36 files: 18 PNG + 18 PDF)

> Full figure checksums are in `results/archive_figures/checksums.sha256` (66 entries).  
> The authoritative archive-level hashes are reproduced here for cross-reference.

| SHA-256 | File Path |
|---|---|
| `7f680b56e7874aeca6bb95872d0360dc9c4e33cbff7febb313f27d3f185dbba9` | `results/archive_figures/primary_pipeline/Fig1_AnnualTimeSeries.png` |
| `1a1c06b44960664526058ff5fe9c40995837ddcfe78ffcf3ba3b5df5a1d693ae` | `results/archive_figures/primary_pipeline/Fig1_AnnualTimeSeries.pdf` |
| `3fc6772c7247b5002dd193c1e7ee25bff0787ff486384bce352b55e13e9dc60c` | `results/archive_figures/primary_pipeline/Fig2_WetDryTimeSeries.png` |
| `76d1279d34a504ef8362d54c8075741713139bfab7082266d874e694903b80e6` | `results/archive_figures/primary_pipeline/Fig2_WetDryTimeSeries.pdf` |
| `3b476888a9e8c52d6e273f8be71b7ba7ce2fb1ff52070c4d0353c83912e9fdf9` | `results/archive_figures/primary_pipeline/Fig3_SenSlope_AllScales.png` |
| `9792f6b697d2b8b3bc85cb6911ec95ad44332a928bb07aa2e8b61f915465727f` | `results/archive_figures/primary_pipeline/Fig3_SenSlope_AllScales.pdf` |
| `dbd518e82e10a7d42a77004a1c758e5daad17735800717dd595aeae36bab39d3` | `results/archive_figures/primary_pipeline/Fig4_MK_vs_MMK_Comparison.png` |
| `25e7c3543399f87384ff6d9c6abecd566b38b72b4326f99db5068483dcc09912` | `results/archive_figures/primary_pipeline/Fig4_MK_vs_MMK_Comparison.pdf` |
| `be06cf907e258a763b25c0f2372494e355ed0365cc84f22601ff1cf1c63af388` | `results/archive_figures/primary_pipeline/Fig5_Significance_Heatmap.png` |
| `48760e4e3699028458fca782333d0edb7202ddf4b27444873d655a0fa84ede00` | `results/archive_figures/primary_pipeline/Fig5_Significance_Heatmap.pdf` |
| `7e24ef3a024adb39ccdaf88dec40dbadf7989160ff4aa030bac71187d47dee29` | `results/archive_figures/primary_pipeline/Fig6_Autocorrelation.png` |
| `544abe83c0f8c4647e4c44ea88e3f7b7e3e16728442e06bbe2e152440776cee8` | `results/archive_figures/primary_pipeline/Fig6_Autocorrelation.pdf` |
| `dcb6ace99183e885e79db08a1d22a190c053203685174abe6335123cf0eeff1b` | `results/archive_figures/primary_pipeline/Fig7_MonthlyClimatology.png` |
| `5edb00577ea370873b8e05695b14546e987754244caf03a6b90d6965727f2bef` | `results/archive_figures/primary_pipeline/Fig7_MonthlyClimatology.pdf` |
| `e7dceb22b057596eddb3231f461fe06dbd6d0a0e89c04297e16baa606b0a59f2` | `results/archive_figures/primary_pipeline/Fig8_SpatialTrend_Summary.png` |
| `0b2a052a45e45c34e810fe6509150d3e755a9fe8a9a725f8aff257da3e6c5aae` | `results/archive_figures/primary_pipeline/Fig8_SpatialTrend_Summary.pdf` |
| `9b4af80a703c228de239c197342dc70ded1bf3dba2a966c185456f29146243ed` | `results/archive_figures/primary_pipeline/Fig9_TaylorDiagram.png` |
| `5d8e4047694f390a351d66718d11a9094440df0eeccc56d95618cb666214f51b` | `results/archive_figures/primary_pipeline/Fig9_TaylorDiagram.pdf` |
| `83ae336cbd46a22b0d90595f5c1476c63f4b650563f11a219c08207ae7a69886` | `results/archive_figures/primary_pipeline/Fig10_ZComparisonMatrix.png` |
| `85c3b5e888c069741ce836dd168d3fab0194ce2c75c8153525f1790e5f04f790` | `results/archive_figures/primary_pipeline/Fig10_ZComparisonMatrix.pdf` |
| `9f37a0bd82d3029e3ca1e205fdf9cfd71bfa7655f9a7ad0d41a2f0e93a958e1f` | `results/archive_figures/primary_pipeline/Fig11_MethodComparison.png` |
| `eb024d15ef4ed9aa105462be2b77310270c90826985d85f66eacd4ebe0b808a8` | `results/archive_figures/primary_pipeline/Fig11_MethodComparison.pdf` |
| `ea5cfdec49373b957cd05e3779827ad4f2dd89f7f1297adb4de8d76881e6d9a1` | `results/archive_figures/primary_pipeline/Fig12_ACF_Diagnostics.png` |
| `1c9fe10dcb51a49b20924de4f644b3f25977bde59ff15d2b0923924e6b9b8b45` | `results/archive_figures/primary_pipeline/Fig12_ACF_Diagnostics.pdf` |
| `998b07d170208064e1c341c3c22738038139e5f8e4c9f7b8aa552d76db294cd1` | `results/archive_figures/primary_pipeline/Fig13_FieldSignificance.png` |
| `dc71429f9a4f35207aa0843a24d844fc9f8a9572eb9a772862fbfe6c9ce95069` | `results/archive_figures/primary_pipeline/Fig13_FieldSignificance.pdf` |
| `679895a677d610d6b9b2e0457cf9635217aa4fa9765a85b0dce7fc2532369504` | `results/archive_figures/primary_pipeline/Fig14_SpatialMaps.png` |
| `45068f4175534859121a58be95796da1e3b0dfcfbcec1c2843cda909aa8fd7f2` | `results/archive_figures/primary_pipeline/Fig14_SpatialMaps.pdf` |
| `02331d3b4decea54db21a602213e92facb7b52cfe8a18896b6b69b9173fe9559` | `results/archive_figures/primary_pipeline/Fig_SpatialStation.png` |
| `a60059deed11a5f3d5016d92f6eaf2a219d853fe2c76de572d8816a0137c20b5` | `results/archive_figures/primary_pipeline/Fig_SpatialStation.pdf` |
| `07b4ce1aad0f8991c6fc298fb7c8a803373051e542cfd2183b96d9c50da1e4ee` | `results/archive_figures/primary_pipeline/Fig_SpatialMethods.png` |
| `ade149c4f766b63a08ec8d7f07d518ec586288d73913c4b7aae07fa95f489a66` | `results/archive_figures/primary_pipeline/Fig_SpatialMethods.pdf` |
| `57b3da39d238e5246823624d2afdc81a7f2747cd837f99847dd872c28056974f` | `results/archive_figures/primary_pipeline/Fig_SpatialFieldSig.png` |
| `9d4570efd8f673d241c9c792af1df3a2cab6ef8ff7bd5ad3906d42ea34cfd66d` | `results/archive_figures/primary_pipeline/Fig_SpatialFieldSig.pdf` |
| `c51706352cd1ab5a4ec8a4ab7c40e4c85017bb990eda7b4b58474bcf3dddb5a6` | `results/archive_figures/primary_pipeline/Fig_SpatialFull.png` |
| `278d24ad6adfe48eaaf094f9ddd22f3b6436c959a85ca84f892e3bcf88e88f39` | `results/archive_figures/primary_pipeline/Fig_SpatialFull.pdf` |

---

## Archived Figures — Comparison Figures (30 files: 10 PNG + 10 PDF + 10 SVG)

| SHA-256 | File Path |
|---|---|
| `2b14d23ff9ad3b0d2a60dde2bb2a7e10d043979706bbf696fcea96b44908fa4a` | `results/archive_figures/comparison_figures/Figure_01_Agreement_Heatmap.png` |
| `938961ffe2c354b0860df009fcec8d7f76e565ed3a114e25605f42d7b3d3178f` | `results/archive_figures/comparison_figures/Figure_01_Agreement_Heatmap.pdf` |
| `751f3fc6cfeebfcfb90f5ea19c69e3ad61c84b302ed8b3ecd414f017cb8a0761` | `results/archive_figures/comparison_figures/Figure_01_Agreement_Heatmap.svg` |
| `f0978fdcad3aeaa1136e7a3cf8a0e0fe18ed812502aa6fb0dcf3656dab444be3` | `results/archive_figures/comparison_figures/Figure_02_MK_vs_MMK_Scatter.png` |
| `acd3c6559b2b9eeb3b6066f119b59eff3688bcc1100e4b7f4ff0a635a4807ad9` | `results/archive_figures/comparison_figures/Figure_02_MK_vs_MMK_Scatter.pdf` |
| `1e7ad1b02beb382c8ed83cab57cf94cbfec87762e8f0fe6524a91bc499050724` | `results/archive_figures/comparison_figures/Figure_02_MK_vs_MMK_Scatter.svg` |
| `bd4b4bb7b21b8d90e1a7a58dbcd8f0758bb2d02deeb275ecff567b4e57433e0e` | `results/archive_figures/comparison_figures/Figure_03_MK_vs_PW_Scatter.png` |
| `38273a575bfadbfcd67d4e97fd7fa4b6ac247fca9bb6446430a4f5fb22e37e26` | `results/archive_figures/comparison_figures/Figure_03_MK_vs_PW_Scatter.pdf` |
| `181909f7881df964f796108a7121e245740210271439ba58200e14043f72d70e` | `results/archive_figures/comparison_figures/Figure_03_MK_vs_PW_Scatter.svg` |
| `6d9eebeba1f3dcd15e3422a9f516f1558e3cf6d31d9219368b5d42f4191a8608` | `results/archive_figures/comparison_figures/Figure_04_MK_vs_TFPW_Scatter.png` |
| `06bae35d36939ef078ac2d64a9b82ced5ed3c4b61e15dff29cb1e3a664627ec6` | `results/archive_figures/comparison_figures/Figure_04_MK_vs_TFPW_Scatter.pdf` |
| `dcf244a818e4920175b6a022fbedf35e6a28c70f1ee586bb af04bec8805658ea` | `results/archive_figures/comparison_figures/Figure_04_MK_vs_TFPW_Scatter.svg` |
| `7b2b2b59d781b33125595120f9c68cbb011b6d90bac0d381f9d81e03c40ff6c5` | `results/archive_figures/comparison_figures/Figure_05_DeltaZ_Boxplots.png` |
| `44239a249461f8c5bae5296d13f6cb0d1ef3d6189c20e3294d09f09a5ecf76eb` | `results/archive_figures/comparison_figures/Figure_05_DeltaZ_Boxplots.pdf` |
| `db1079c28cb67fd5adec7a4784b95624290e9f3752bf17679cc36fe6c0d502da` | `results/archive_figures/comparison_figures/Figure_05_DeltaZ_Boxplots.svg` |
| `4a065a27b02eb74343de81ab40845dcdfbff19a8533993339750422992cfca33` | `results/archive_figures/comparison_figures/Figure_06_CorrectionFactor_Distribution.png` |
| `04353d02a5b45f3af510584c46ad0747dde2de8aad57c4d70daf29a5f9907ee7` | `results/archive_figures/comparison_figures/Figure_06_CorrectionFactor_Distribution.pdf` |
| `1e6454a0c1e7cecc8e96aac915ba1a67e2dab704ace8aeb84ed6aef749eb6dbc` | `results/archive_figures/comparison_figures/Figure_06_CorrectionFactor_Distribution.svg` |
| `58b3b2dab6c886820743622fac0594095406b022ec677db5586fadfc895061c3` | `results/archive_figures/comparison_figures/Figure_07_nEff_Distribution.png` |
| `653114da1c92bfae3b727cab6e61be9c2770f71b1e6df262a795418607af1b4b` | `results/archive_figures/comparison_figures/Figure_07_nEff_Distribution.pdf` |
| `c8e68db7ad79435993c3bbdcc47b3de94e0c46b616612f94e5027cd04373527d` | `results/archive_figures/comparison_figures/Figure_07_nEff_Distribution.svg` |
| `ab31d505cd8436e72819ec9f74e42d223067fe5b77941a48c08cfe75cd4d127d` | `results/archive_figures/comparison_figures/Figure_08_Field_Significance_Comparison.png` |
| `a78d7a53d9f275dc2ab7af12f1760bed95b565d170557efb7d42297e4c04f21b` | `results/archive_figures/comparison_figures/Figure_08_Field_Significance_Comparison.pdf` |
| `378502cedcedb33b1bcfe1e5d02c5ea1f9227062c5deba4c58df7e895501f86d` | `results/archive_figures/comparison_figures/Figure_08_Field_Significance_Comparison.svg` |
| `641d068169b81296ae93501a09fc21c1602cd1b9911caec7e2a9577329683a99` | `results/archive_figures/comparison_figures/Figure_09_Significance_Transition_Matrix.png` |
| `3363b73e6e893c88f18cd5ec81c25c04bcca6697b12344d6f6cf0dbb394dcb90` | `results/archive_figures/comparison_figures/Figure_09_Significance_Transition_Matrix.pdf` |
| `bd1408da9e3449c58823a1e3ac16d2b4277303d7f7d884c5d52c48c9f35b0dde` | `results/archive_figures/comparison_figures/Figure_09_Significance_Transition_Matrix.svg` |
| `09444376049e646d98b0b6ce2a928e43298ca9f071942d4c0bab81e8cd01e581` | `results/archive_figures/comparison_figures/Figure_10_Method_Ranking_Summary.png` |
| `54979d2be3e9ef8aef8caff1e60a52f8a7a0693dc0afbf04c0c06c31879ba853` | `results/archive_figures/comparison_figures/Figure_10_Method_Ranking_Summary.pdf` |
| `d8135fea702fa17a7daa099f43907c183ed81790ad2e02275f6a8cc3506f5735` | `results/archive_figures/comparison_figures/Figure_10_Method_Ranking_Summary.svg` |

---

## Checksum Verification Commands

```bash
# Verify a single file
sha256sum -c <(echo "f845a0248d3a2008e1d239fe04f63043f023445d077d5ee2c63e86203f498457  Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv")

# Verify all archived figures (using the dedicated checksum file)
cd results/archive_figures/
sha256sum -c checksums.sha256

# Verify all committed files at once
git ls-files | xargs sha256sum | sort > /tmp/current_hashes.txt
# Compare to this document manually or via diff against a saved baseline
```

---

*Generated from committed file state at branch HEAD (9b99b81). Files added after this commit will not appear in this table.*
