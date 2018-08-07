#!/usr/bin/python3

import bibtexparser
import click
import pprint
import datetime
import os
import pprint
import glob
import pypandoc

VERBOSE = False

def create_entry(entry):
    key = entry['ID'] if 'ID' in entry else '-'
    added = entry['added'] if 'added' in entry else '-'
    scheduled = entry['scheduled'] if 'scheduled' in entry else '-'
    annote = entry['annote'] if 'annote' in entry else ''
    keywords = ''
    keywords = ','.join([keywords, entry['keyword'] if 'keyword' in entry else ''])
    keywords = ','.join([keywords, entry['keywords'] if 'keywords' in entry else ''])
    keywords = keywords.strip(',')
    file = entry['file'].strip(':') if 'file' in entry else ''

    txt = """* [@{0}]
------

    **Keywords**: {1}""".format(key, keywords.lower())

    if annote:
        txt += '\n'

        for note in annote.split(','):
            txt += """
    * {}""".format(note.strip())

    txt += '\n'

    txt += '\n\t**Meta:**'

    if file:
        txt += " [PDF]({})".format(file)
        txt += ','
    txt += " key: {}".format(key)

    txt += '\n\n'

    return txt

def create_main_bib(basedir, ignorebib):
    bibfiles = glob.iglob(os.path.join(basedir, '**/*.bib'), recursive=True)
    bibfiles = filter(lambda x: x[len(basedir.rstrip('/'))+1:] not in ignorebib, bibfiles)

    with open(os.path.join(basedir, 'main.bib'), 'w') as main:
        for bibfile in bibfiles:

            if VERBOSE:
                print('process bibfile {}'.format(bibfile))

            with open(bibfile, 'r') as f:

                db = bibtexparser.load(f)
                entries = db.entries
                if len(entries) == 0: continue
                entry = entries[0]

                folder = bibfile[len(basedir.rstrip('/'))+1:].split(os.path.sep)[0]

                # See if corresponding pdf file exists, if true add location
                if 'file' in entry: del(entry['file'])
                basename = os.path.basename(bibfile)
                filename = os.path.splitext(basename)[0]
                pdf_file =  filename + '.pdf'
                if os.path.exists(os.path.join(basedir, folder, pdf_file)):
                    entry['file'] = ':' + os.path.join('.', folder, pdf_file)

                # Add folder (category) as field
                entry['category'] = folder.lower()
                #  entry['category'] = bibfile[len(basedir.rstrip('/'))+1:].split(os.path.sep)[0].lower()

                main.write(bibtexparser.dumps(db))

def create_markdown(tags, basedir, outfile):
    with open(os.path.join(basedir, 'main.bib'), 'r') as f:
        db = bibtexparser.load(f)

    entries = db.entries
    categories = {x['category']: [] for x in entries}

    for entry in entries:
        etags = []
        for etag in [entry[key] for key in ['keyword', 'keywords'] if key in entry]:
            etags.extend(etag.split(','))
            etags = [x.lower().strip() for x in etags]
        if all(elem in etags for elem in tags):
            categories[entry['category']].append(entry)

    with open(os.path.join(basedir, outfile + '.md'), 'w') as f:
        for category_key, category_values in categories.items():
            if len(category_values) == 0: continue
            f.write('# ' + category_key + '\n\n')
            for entry in category_values:
                etags = []
                # for etag in [entry[key] for key in ['keyword', 'keywords'] if key in entry]:
                #     etags.extend(etag.split(','))
                #     etags = [x.lower().strip() for x in etags]
                # if all(elem in etags for elem in tags):
                f.write(create_entry(entry))

        f.write('# References')

def create_html(basedir, infile):
    outfile = infile + '.html'

    filters = ['pandoc-citeproc']
    extra_args = [
        '--bibliography=' + os.path.join(basedir, 'main.bib'),
        '--csl=' + os.path.join(os.path.realpath(__file__), '..', 'assets' 'chicago-author-date.csl'),
        '-s',
    ]

    pypandoc.convert_file(os.path.join(basedir, infile + '.md'),
                          'html',
                          outputfile=os.path.join(basedir, outfile),
                          extra_args=extra_args,
                          filters=filters,
                         )

@click.command()
@click.option('--basedir', type=str, default='', help='basedir')
@click.option('--ignorebib', type=list, default=[], help='ignore additional bibfiles')
@click.option('--verbose/--no-verbose', default=False)
def main(basedir, ignorebib, verbose):

    global VERBOSE
    VERBOSE = verbose

    exclude_bibs = ['main.bib']

    exclude_bibs += ignorebib

    create_main_bib(basedir, exclude_bibs)
    create_markdown(['reading club'], basedir, 'reading_club')
    create_html(basedir, 'reading_club')

    create_markdown(['journal club'], basedir, 'journal_club')
    create_html(basedir, 'journal_club')

    create_markdown(['todo'], basedir, 'todo')
    create_html(basedir, 'todo')

    create_markdown([], basedir, 'all')
    create_html(basedir, 'all')

if __name__ == '__main__':
    main()
