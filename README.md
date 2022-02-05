# COVID-MVP

SARS-CoV-2 Variants of Concern (VOC) & Interest (VOI) pose high risks to global
public health. COVID-MVP tracks mutations from VOCs and VOIs to enable
interactive visualization in near-real time. COVID-MVP has 3 modules: A
Nextflow-wrapped workflow ([nf-ncov-voc][nf-ncov-voc]) for identifying mutations
in genomic data; a Python module that integrates functional annotations from the
[Pokay repository][pokay], based on literature curation; and an interactive
visualization for prevalence of mutations in variants and their functional
impact, based on Dash & Plotly frameworks.

You can find a deployed version of this application (without user upload
functionality) at [https://covidmvp.cidgoh.ca/][deployed].

[deployed]: https://covidmvp.cidgoh.ca/

![app_interface]

[app_interface]: screenshots/app_interface.png

## Installation

###_0. (For users that plan to upload their own data)_ [Install Nextflow][nf]

[nf]: https://www.nextflow.io/docs/latest/getstarted.html

### 1. Clone the repository and its submodules

`$ git clone git@github.com:cidgoh/COVID-MVP.git`

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

Click the legend button ![legend_btn] at the top for an in-app explanation of
the heatmap view.

[legend_btn]: screenshots/legend_btn.png

![legend_btn_click]

[legend_btn_click]: screenshots/legend_btn_click.gif

### Heatmap view

The left axis encodes variants. VOC are in **bold**, and VOI are in _italics_.

The right axis encodes the number of genomic sequences analyzed for each
variant.

The top axis encodes the nucleotide position of variant mutations, with respect
to the [reference SARS-CoV-2 genome][wuhan] from Wuhan.

[wuhan]: https://www.ncbi.nlm.nih.gov/nuccore/NC_045512.2

The bottom axis encodes the amino acid position of variant mutations, in the
following format:

**Genic mutations:** `{GENE}.{AMINO ACID POSITION WITHIN THAT GENE}`

**Intergenic:** `{NEAREST DOWNSTREAM GENE}. {NUMBER OF NUCLEOTIDES UPSTREAM}`

The heatmap cells encode the presence of mutations. The color of these cells
encodes mutation frequency. Insertions,  deletions, functional mutations, and
variants with a sample size of one are indicated as follows:

![heatmap_cells]

[heatmap_cells]: screenshots/heatmap_cells.png

Hovering over cells displays detailed mutation information. Clicking cells opens
a modal with detailed mutation function descriptions, and their citations.

![scroll_hover_click]

[scroll_hover_click]: screenshots/heatmap_scroll_hover_click.gif

### Histogram

The histogram bars encode the total number of mutations across all VOI/VOC every
100 nucleotide positions. The horizontal bar directly under the histogram bars
maps SARS-CoV-2 genes to the histogram x-axis. The black horizontal bar at the
bottom maps the current position of the heatmap viewport to the SARS-CoV-2
genome.

![histogram_hover_scroll]

[histogram_hover_scroll]: screenshots/histogram_hover_scroll.gif

### Table

A tabular subset of fields for a single VOI/VOC, modified from the application
data used to generate the heatmap and histogram views. You can alternate between
variants by clicking on the heatmap cells.

![table_interface]

[table_interface]: screenshots/table_interface.png

### Editing the visualization

There are several tools in the top of the interface that can be used to edit the
visualization.

Clicking the select lineages btn ![select_lineages_btn] opens a modal that
allows you to rearrange and hide variants.

[select_lineages_btn]: screenshots/select_lineages_btn.png

The mutation frequency slider allows you to filter heatmap cells by mutation
frequency.

![mutation_freq_slider]

[mutation_freq_slider]: screenshots/mutation_freq_slider.gif

The clade defining switch allows you to filter in and out heatmap cells
corresponding to non-clade defining mutations.

![clade_defining_switch]

[clade_defining_switch]: screenshots/clade_defining_switch.gif

#### Uploading data

The upload button ![upload_btn] allows you to upload your own SARs-CoV-2 genomic
data in `FASTA` or `VCF` format.  You can find examples of files users can
upload in [test_data/][3].

[upload_btn]: screenshots/upload_btn.png
[3]: test_data/

_You must have Nextflow installed to upload files._

#### Downloading data

The download button ![download_btn] allows you to download a zip object
containing surveillance reports for each reference variant. You can find
examples of these reports in [surveillance_reports/][4].

[download_btn]: screenshots/download_btn.png
[4]: surveillance_reports/

## [nf-ncov-voc][nf-ncov-voc]

This pipeline generates the data files for the visualization.

## [pokay][pokay]

Stand-alone repository of functional annotations, that we use as an annotation
source in this application.

[nf-ncov-voc]: https://github.com/cidgoh/nf-ncov-voc/
[pokay]: https://github.com/nodrogluap/pokay/

## Support

We encourage you to add any problems with the application as an issue in this
repository, but if you need to contact us by email, you can email us at
contact@cidgoh.ca.

## Authors and acknowledgement

[@ivansg44][ivan]: Visualization development

[@Anoosha-Sehar][anoosha]: Functional annotation

[@anwarMZ][zohaib]: Genomic analysis

[@miseminger][madeline]: Functional annotation and data standardization

[@despean][kenyi]: Application deployment

[ivan]: https://github.com/ivansg44
[anoosha]: https://github.com/Anoosha-Sehar
[zohaib]: https://github.com/anwarMZ
[madeline]: https://github.com/miseminger
[kenyi]: https://github.com/despean

William Hsiao, Gary Van Domselaar, and Paul Gordon

The results here are in whole or part based upon data hosted at the Canadian
VirusSeq Data Portal: https://virusseq-dataportal.ca/. We wish to acknowledge
the following organisations/laboratories for contributing data to the Portal:
Canadian Public Health Laboratory Network (CPHLN), CanCOGGeN VirusSeq,
Saskatchewan - Roy Romanow Provincial Laboratory(RRPL), Nova Scotia Health
Authority, Alberta ProvLab North(APLN), Queen's University / Kingston Health
Sciences Centre, National Microbiology Laboratory(NML), BCCDC Public Health
Laboratory, Public Health Ontario(PHO), Newfoundland and Labrador - Eastern
Health, Unity Health Toronto, Ontario Institute for Cancer Research(OICR),
Manitoba Cadham Provincial Laborator, and Manitoba Cadham Provincial Laboratory.

## License

[MIT][5]

[5]: LICENSE
