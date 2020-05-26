import subprocess
import os

#Third party
import bibtexparser
from bibtexparser.bparser import BibTexParser
import inquirer
import ads

from . import config

ads.config.token = config.config['ADS']['token']



def get_bibtex_from_ADS(arg_dict):

    papers = ads.SearchQuery(**arg_dict)
    papers = [paper for paper in papers]

    if len(papers) == 0:
        print('No papers found in ADS')
        return
    opts_ = []

    max_res = int(config.config['ADS']['max results'])

    if len(papers) > max_res:
        papers = papers[:max_res]

    for paper in papers:
        if len(paper.author) > 1:
            et_al = 'et. al '
        else:
            et_al = ''
        opts_ += [f'{paper.author[0]} {et_al}[{paper.year}]: {paper.title}' ]

    questions = [
        inquirer.Checkbox('ads',
            message="Add to bibtex and attempt PDF fetch?",
            choices=opts_,
        ),
    ]
    answers = inquirer.prompt(questions)

    save_papers = []
    for ans in answers['ads']:
        save_papers.append(papers[opts_.index(ans)])

    if len(save_papers) == 0:
        return 

    papers = save_papers
    del save_papers

    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    parser.homogenise_fields = False

    bibcodes = [paper.bibcode for paper in papers]

    bibtex_data = bibtex_query = ads.ExportQuery(
        bibcodes=bibcodes,
        format='bibtex',
    ).execute()

    bib_database = bibtexparser.loads(bibtex_data, parser)

    return bib_database, bibcodes


def get_PDF_from_ADS(bibcodes, bib_ids):
    for bibcode, bib_id in zip(bibcodes, bib_ids):
        paper_path = config.PAPERS_FOLDER / f'{bib_id}.pdf'
        if paper_path.exists():
            continue

        cmd = ['curl',
            '-H',
            f'Authorization: Bearer {config.config["ADS"]["token"]}',
            f'https://ui.adsabs.harvard.edu/link_gateway/{bibcode}/ADS_PDF',
            '-L',
            '-o',
            str(paper_path),
        ]
        subprocess.run(cmd)

        print('First lines of content:')
        lines = 0
        with open(paper_path, 'r') as f:
            for line in f:
                print(line.strip())
                lines += 1
                if lines > 10:
                    break

        questions = [
            inquirer.List('keep',
                message="Keep the file?",
                choices=['Yes', 'No'],
            ),
        ]
        answers = inquirer.prompt(questions)

        if answers['keep'] == 'No':
            os.remove(paper_path)
