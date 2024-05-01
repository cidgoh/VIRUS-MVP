# VIRUS-MVP

Viral lineages and variants pose high risk to global public health.

VIRUS-MVP is a heatmap-centric visualization web application that encodes
mutational information across multiple groups, including SARS-CoV-2 lineages.
The data visualized by VIRUS-MVP is generated by two external projects:

* [nf-ncov-voc][nf-ncov-voc]
* [Pokay][pokay]

You can find deployed versions of this application (without user upload
functionality) at https://virusmvp.org/.

![app_interface]

[app_interface]: screenshots/app_interface.png

## Installation

### _0. (If uploading your own data)_ Install [Nextflow][nf] & [Conda][conda].

[nf]: https://www.nextflow.io/docs/latest/getstarted.html
[conda]: https://conda.io/projects/conda/en/latest/user-guide/install/

### 1. Clone the repository and its submodules

`$ git clone git@github.com:cidgoh/VIRUS-MVP.git --recurse-submodules`

### 2. Create a virtual environment

We use [Conda](https://docs.conda.io/en/latest/), but you can use
[venv](https://docs.python.org/3/library/venv.html).

`$ conda create --name=VIRUS-MVP`

### 3. Activate the environment

`$ conda activate VIRUS-MVP`

### 4. Install requirements

`(VIRUS-MVP) $ pip install -r requirements.txt`

### 5. Run the application

If you do not run the application from the root directory,
some of the JavaScript assets will not be compiled.

`(VIRUS-MVP) $ python app.py`

Go to http://0.0.0.0:8050/.

## Usage

Click the help button ![help_btn] at the top for an in-app explanation of the
heatmap view.

[help_btn]: screenshots/help_btn.png

![legend]

[legend]: screenshots/legend.png

### Heatmap view

The left axis encodes viral lineages. Lineages belonging to VOC are in
**bold**, and lineages belonging to VOI are in _italics_. Actively circulating
lineages are denoted with ⚠️.

The right axis encodes the number of genomic sequences analyzed for each
lineage.

The top axis encodes the nucleotide position of lineage mutations, with respect
to the reference genome.

The bottom axis encodes the amino acid position of lineage mutations, in the
following format:

**Genic mutations:** `{GENE}.{AMINO ACID POSITION WITHIN THAT GENE}`

**Intergenic:** `{NEAREST DOWNSTREAM GENE}. {NUMBER OF NUCLEOTIDES UPSTREAM}`

The heatmap cells encode the presence of mutations. The color of these cells
encodes mutation frequency. Insertions,  deletions, functional mutations, and
lineages with a sample size of one are encoded as follows:

![heatmap_cells]

[heatmap_cells]: screenshots/heatmap_cells.png

Hovering over cells displays detailed mutation information. Clicking cells opens
a modal with detailed mutation function descriptions, and their citations.

![scroll_hover_click]

[scroll_hover_click]: screenshots/heatmap_scroll_hover_click.gif

### Histogram

The histogram bars encode the total number of mutations across all visualized
lineages every 100 nucleotide positions.

![histogram_hover_scroll]

[histogram_hover_scroll]: screenshots/histogram_hover_scroll.gif

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

The upload button ![upload_btn] allows you to upload your own genomic data in
`FASTA` or `VCF` format.  You can find examples of files users can upload in
[test_data/][3].

[upload_btn]: screenshots/upload_btn.png
[3]: test_data/

_You must have Nextflow and Conda installed to upload files._

_Your first upload will take a while. Subsequent uploads will be faster._

#### Downloading data

The download button ![download_btn] allows you to download a zip object
containing surveillance reports for each reference variant. You can find
examples of these reports in [surveillance_reports/][4].

[download_btn]: screenshots/download_btn.png
[4]: surveillance_reports/

## [nf-ncov-voc][nf-ncov-voc]

Nextflow-wrapped workflow for variant calling.

## [pokay][pokay]

Repository for mutation functions.

[nf-ncov-voc]: https://github.com/cidgoh/nf-ncov-voc/
[pokay]: https://github.com/nodrogluap/pokay/

## Support

We encourage you to add any problems with the application as an issue in this
repository, but you can also email us at contact@cidgoh.ca.

## Authors and acknowledgement

[@ivansg44][ivan]: Visualization development

[@anwarMZ][zohaib]: Genomic analysis

[@Anoosha-Sehar][anoosha]: Functional annotation

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
