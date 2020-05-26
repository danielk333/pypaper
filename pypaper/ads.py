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

        sources = ['EPRINT_PDF', 'ADS_PDF', 'PUB_PDF']
        for source in sources:
            cmd = ['curl',
                '-H',
                f'Authorization: Bearer {config.config["ADS"]["token"]}',
                f'https://ui.adsabs.harvard.edu/link_gateway/{bibcode}/{source}',
                '-L',
                '-o',
                str(paper_path),
            ]
            subprocess.run(cmd)

            lines = 0
            keep_ = True
            try:
                with open(paper_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if lines == 4:
                            if line.strip() == '<title>Error</title>':
                                keep_ = False
                            break
                        lines += 1
            except UnicodeDecodeError:
                pass

            if keep_:
                break
            else:
                os.remove(paper_path)
        if keep_:
            print('PDF found and saved to database')
        else:
            print('No PDF source was available')
