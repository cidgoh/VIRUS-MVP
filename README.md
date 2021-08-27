# COVID-MVP

SARS-CoV-2 Variants of Concern (VOC) & Interest (VOI) pose high risks to global
public health. COVID-MVP tracks mutations from VOCs and VOIs to enable
interactive visualization in near-real time. COVID-MVP has 3 modules: A
Nextflow-wrapped workflow for identifying mutations in genomic data; a Python
module for functional annotation, based on literature curation; and an
interactive visualization for prevalence of mutations in variants and their
functional impact, based on Dash & Plotly frameworks.

![app_interface]

[app_interface]: screenshots/app_interface.png

## Installation

### 1. Clone the repository and its submodules

`$ git clone git@github.com:cidgoh/COVID-MVP.git --recurse-submodules`

### 2. Create a virtual environment

We use [Conda][conda], but you can use [venv][venv]. We
recommend using Python 3.9 in your virtual environment. Older Python versions
may break the application.

[conda]: https://docs.conda.io/en/latest/
[venv]: https://docs.python.org/3/library/venv.html

`$ conda create --name=COVID-MVP python=3.9`

### 3. Activate the environment

`$ conda activate COVID-MVP`

### 4. Install requirements

`(COVID-MVP) $ pip install -r requirements.txt`

### 5. Run the application

If you do not run the application from the root directory,
some of the JavaScript assets will not be compiled.

`(COVID-MVP) $ python app.py`

Go to http://127.0.0.1:8050/.

## Usage

TODO: visuals

### Heatmap view

The y-axis encodes VOI/VOC. The x-axis encodes nucleotide position on the top,
and amino acid position on the bottom. Amino acid position is described in the
following notations:

**Genic:** `{GENE}.{AMINO ACID POSITION WITHIN THAT GENE}`

**Intergenic:** `{NEAREST DOWNSTREAM GENE}.{NUMBER OF NUCLEOTIDES UPSTREAM}`

The heatmap cells encode the presence of mutations. The color of these cells
encodes mutation frequency. Insertions and deletions are annotated with markers.

Hovering over cells displays detailed mutation information.

Clicking cells opens a modal with detailed mutation function descriptions, and
their citations.

### Histogram

The histogram bars encode the total number of mutations across all VOI/VOC every
100 nucleotide positions. The horizontal bar directly under the histogram bars
maps SARS-CoV-2 genes to the histogram x-axis. The black horizontal bar at the
bottom maps the current position of the heatmap viewport to the SARS-CoV-2
genome.

### Table

A tabular subset of fields for a single VOI/VOC, modified from the application
data used to generate the heatmap and histogram views. You can alternate between
VOI/VOI by clicking on the heatmap cells.

### Editing the visualization

There are several tools in the top of the interface that can be used to edit the
visualization.

The select lineages modal allows yoi to rearrange and hide VOI/VOC.

The upload button allows you to upload data on additional VOI/VOC in gvf format.
You can find examples of files users can upload in [test_data/][3].

[3]: test_data/

The mutation frequency slider allows you to filter heatmap cells by mutation
frequency.

The clade defining switch allows you to filter in and out heatmap cells
corresponding to non-clade defining mutations.

### Submodules

#### [nf-ncov-voc][nf-ncov-voc]

This pipeline generates the input files for the visualization. You can run the
pipeline commands from the root COVID-MVP directory.

#### [pokay][pokay]

Repository of functional annotations used in this application.

[nf-ncov-voc]: https://github.com/cidgoh/nf-ncov-voc/
[pokay]: https://github.com/nodrogluap/pokay/

## Authors and acknowledgement

[@ivansg44][ivan]: Visualization development

[@Anoosha-Sehar][anoosha]: Functional annotation

[@anwarMZ][zohaib]: Genomic analysis

[@miseminger][madeline]: Functional annotation and data standardization

[ivan]: https://github.com/ivansg44
[anoosha]: https://github.com/Anoosha-Sehar
[zohaib]: https://github.com/anwarMZ
[madeline]: https://github.com/miseminger

William Hsiao, Gary Van Domselaar, and Paul Gordon

## License

TODO: wait until ready for deployment
