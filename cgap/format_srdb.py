#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess as sp

from Bio import SeqIO

from .make_paths import get_blast_db_path


def fastq_to_fasta(fastq_path):
    """ Yields out fasta records from fastq file """
    with open(fastq_path) as input_handle:
        for record in SeqIO.parse(input_handle, 'fastq'):
            yield record.format('fasta')


def run_format_cmd(fastq):
    """ Runs a blast database format on fasta records
    from biopython """
    db_name = get_blast_db_path(fastq)
    format_cmd = ['formatdb',
                  '-i', 'stdin',
                  '-n', db_name,
                  '-p', 'F']

    p1 = sp.Popen(format_cmd, stdin=sp.PIPE)

    fasta_generator = fastq_to_fasta(fastq)

    for fasta_record in fasta_generator:
        p1.stdin.write(fasta_record.encode())

    p1.stdin.close()
    p1.communicate()

    return True
