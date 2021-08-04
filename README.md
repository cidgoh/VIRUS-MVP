# COVID-MVP

...description

![2]

[2]: screenshots/app_interface.png

## Installation

Create a virtual environment. We use [Conda][0], but you can use [venv][1]. We
recommend using Python 3.9 in your virtual environment. Older Python versions
may break the application.

[0]: https://docs.conda.io/en/latest/
[1]: https://docs.python.org/3/library/venv.html

`$ conda create --name=COVID-MVP python=3.9`

Activate the environment.

`$ conda activate COVID-MVP`

Install requirements.

`(COVID-MVP) $ pip install -r requirements.txt`

Run the application.

`(COVID-MVP) $ python app.py`

Go to http://127.0.0.1:8050/.

## Usage

TODO: visuals

### Heatmap view

The y-axis encodes VOI/VOC. The x-axis encodes nucleotide position on the top,
and amino acid position on the bottom. Amino acid position is described in the
following notation:

`{GENE}.{AMINO ACID POSITION WITHIN THAT GENE}`

The heatmap cells encode the presence of mutations. The color of these cells
encodes mutation frequency. Insertions and deletions are annotated with markers.

Hovering over cells displayed detailed mutation information.

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

## Support

...

## Roadmap

...

## Authors and acknowledgement

...

## License

...
