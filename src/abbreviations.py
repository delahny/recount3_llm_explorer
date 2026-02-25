# abbreviations.py
"""
To handle possible abbreviations in during parsing.
"""

# Cancer
# TCGA OFFICIAL PROJECT CODES {https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/tcga-study-abbreviations}
CANCER = {
    'acc': ['ACC', 'adrenocortical carcinoma'],
    'blca': ['BLCA', 'bladder urothelial carcinoma'],
    'brca': ['BRCA', 'breast invasive carcinoma'],
    'cesc': ['CESC', 'cervical squamous cell carcinoma'],
    'chol': ['CHOL', 'cholangiocarcinoma'],
    'coad': ['COAD', 'colon adenocarcinoma'],
    'dlbc': ['DLBC', 'diffuse large B-cell lymphoma'],
    'esca': ['ESCA', 'esophageal carcinoma'],
    'gbm': ['GBM', 'glioblastoma multiforme'],
    'hnsc': ['HNSC', 'head and neck squamous cell carcinoma'],
    'kich': ['KICH', 'kidney chromophobe'],
    'kirc': ['KIRC', 'kidney renal clear cell carcinoma'],
    'kirp': ['KIRP', 'kidney renal papillary cell carcinoma'],
    'laml': ['LAML', 'acute myeloid leukemia'],
    'lgg': ['LGG', 'brain lower grade glioma'],
    'lihc': ['LIHC', 'liver hepatocellular carcinoma'],
    'luad': ['LUAD', 'lung adenocarcinoma'],
    'lusc': ['LUSC', 'lung squamous cell carcinoma'],
    'meso': ['MESO', 'mesothelioma'],
    'ov': ['OV', 'ovarian serous cystadenocarcinoma'],
    'paad': ['PAAD', 'pancreatic adenocarcinoma'],
    'pcpg': ['PCPG', 'pheochromocytoma and paraganglioma'],
    'prad': ['PRAD', 'prostate adenocarcinoma'],
    'read': ['READ', 'rectum adenocarcinoma'],
    'sarc': ['SARC', 'sarcoma'],
    'skcm': ['SKCM', 'skin cutaneous melanoma'],
    'stad': ['STAD', 'stomach adenocarcinoma'],
    'tgct': ['TGCT', 'testicular germ cell tumor'],
    'thca': ['THCA', 'thyroid carcinoma'],
    'thym': ['THYM', 'thymoma'],
    'ucec': ['UCEC', 'uterine corpus endometrial carcinoma'],
    'ucs': ['UCS', 'uterine carcinosarcoma'],
    'uvm': ['UVM', 'uveal melanoma'],


    # Common cancer abbreviations
    # Breast cancer
    'tnbc': ['TNBC', 'triple-negative breast cancer'],
    'dcis': ['DCIS', 'ductal carcinoma in situ'],
    # Lung cancer
    'nsclc': ['NSCLC', 'non-small cell lung cancer'],
    'sclc': ['SCLC', 'small cell lung cancer'],
    # Colorectal
    'crc': ['CRC', 'colorectal cancer'],
    # Liver
    'hcc': ['HCC', 'hepatocellular carcinoma'],
    # Kidney
    'rcc': ['RCC', 'renal cell carcinoma'],
    # Pancreas
    'pdac': ['PDAC', 'pancreatic ductal adenocarcinoma'],
    # Head and neck
    'hnscc': ['HNSCC', 'head and neck squamous cell carcinoma'],
    'oscc': ['OSCC', 'oral squamous cell carcinoma'],
    'npc': ['NPC', 'nasopharyngeal carcinoma'],
    # Skin
    'scc': ['SCC', 'squamous cell carcinoma'],
    'cscc': ['cSCC', 'cutaneous squamous cell carcinoma'],
    'bcc': ['BCC', 'basal cell carcinoma'],
    'mcc': ['MCC', 'merkel cell carcinoma'],
    'ctcl': ['CTCL', 'cutaneous T-cell lymphoma'],
    # Ovarian
    'hgsoc': ['HGSOC', 'high-grade serous ovarian cancer'],
    # Prostate
    'crpc': ['CRPC', 'castration-resistant prostate cancer'],
    # Brain
    'dipg': ['DIPG', 'diffuse intrinsic pontine glioma'],
    # Leukemias
    'aml': ['AML', 'acute myeloid leukemia'],
    'cml': ['CML', 'chronic myeloid leukemia'],
    'all': ['ALL', 'acute lymphoblastic leukemia'],
    'cll': ['CLL', 'chronic lymphocytic leukemia'],
    'apl': ['APL', 'acute promyelocytic leukemia'],
    'mds': ['MDS', 'myelodysplastic syndrome'],
    # Lymphomas
    'dlbcl': ['DLBCL', 'diffuse large B-cell lymphoma'],
    'hl': ['HL', 'Hodgkin lymphoma'],
    'nhl': ['NHL', 'non-Hodgkin lymphoma'],
    'fl': ['FL', 'follicular lymphoma'],
    'mcl': ['MCL', 'mantle cell lymphoma'],
    # Myeloma
    'mm': ['MM', 'multiple myeloma'],
    # Sarcomas
    'ews': ['EWS', 'Ewing sarcoma'],
    # Neuroendocrine
    'net': ['NET', 'neuroendocrine tumor'],
    'nec': ['NEC', 'neuroendocrine carcinoma']
}

# Non-cancer disease abbreviations
OTHER_DISEASES = {
    'sle': ['SLE', 'systemic lupus erythematosus'],
    'scle': ['SCLE', 'subacute cutaneous lupus erythematosus'],
    'ra': ['RA', 'rheumatoid arthritis'],
    'ibd': ['IBD', 'inflammatory bowel disease'],
    'uc': ['UC', 'ulcerative colitis'],
    'ms': ['MS', 'multiple sclerosis'],
    'copd': ['COPD', 'chronic obstructive pulmonary disease'],
    'ipf': ['IPF', 'idiopathic pulmonary fibrosis'],
    'nafld': ['NAFLD', 'non-alcoholic fatty liver disease'],
    'nash': ['NASH', 'non-alcoholic steatohepatitis'],
    't1d': ['T1D', 'type 1 diabetes'],
    't2d': ['T2D', 'type 2 diabetes'],
    'ad': ['AD', 'Alzheimer disease'],
    'pd': ['PD', 'Parkinson disease'],
    'als': ['ALS', 'amyotrophic lateral sclerosis'],
    'hiv': ['HIV', 'human immunodeficiency virus'],
    'hbv': ['HBV', 'hepatitis B virus'],
    'hcv': ['HCV', 'hepatitis C virus'],
    'tb': ['TB', 'tuberculosis'],
    'covid': ['COVID', 'COVID-19', 'SARS-CoV-2']
}

# Common technique abbreviations
TECHNIQUES = {
    'scrna-seq': ['scRNA-seq', 'scrnaseq', 'single-cell RNA-seq', 'single cell RNA sequencing'],
    'snrna-seq': ['snRNA-seq', 'single-nucleus RNA-seq'],
    'scatac-seq': ['scATAC-seq', 'single-cell ATAC-seq'],
    'atac-seq': ['ATAC-seq', 'chromatin accessibility'],
    'chip-seq': ['ChIP-seq', 'chromatin immunoprecipitation sequencing'],
    'miRNA': ['miRNA', 'microRNA'],
    'wgs': ['WGS', 'whole genome sequencing'],
    'wes': ['WES', 'whole exome sequencing'],
    'wgbs': ['WGBS', 'whole genome bisulfite sequencing'],
    'rrbs': ['RRBS', 'reduced representation bisulfite sequencing'],
    'pcr' : ['PCR', 'polymerase chain reaction'],
    'elisa' : ['ELISA','enzyme-linked immunosorbent assay']
}

# Common cell type abbreviations
CELLTYPES = {
    'treg': ['Treg', 'regulatory T cell'],
    'tregs': ['Tregs', 'regulatory T cells'],
    'nk': ['NK', 'NK cell', 'natural killer cell'],
    'dc': ['DC', 'dendritic cell'],
    'tam': ['TAM', 'tumor-associated macrophage'],
    'mdsc': ['MDSC', 'myeloid-derived suppressor cell'],
    'caf': ['CAF', 'cancer-associated fibroblast'],
    'til': ['TIL', 'tumor-infiltrating lymphocyte'],
    'tils': ['TILs', 'tumor-infiltrating lymphocytes'],
    'pbmc': ['PBMC', 'peripheral blood mononuclear cell'],
    'pbmcs': ['PBMCs', 'peripheral blood mononuclear cells'],
    'hsc': ['HSC', 'hematopoietic stem cell'],
    'msc': ['MSC', 'mesenchymal stem cell'],
    'ipsc': ['iPSC', 'induced pluripotent stem cell'],
    'esc': ['ESC', 'embryonic stem cell'],
}