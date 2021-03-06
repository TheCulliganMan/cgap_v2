#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Pool, cpu_count

import argparse

import cgap


def cgap_parser():
    """ parses command line arguments for cgap """
    parser = argparse.ArgumentParser(
        description='Start cGAP: Script for running \
        Consensus Gene Assembly Program.')

    parser.add_argument(
        '-refs_path',
        action="store",
        dest="refs_path",
        help="The path where cGAP gene references are stored.",
        required=True
    )  # Directory of query files

    parser.add_argument(
        '-forward',
        action="store",
        dest="forward_reads",
        nargs="+",
        help="The FORWARD fastq samples that will be \
        used for the run.",
        required=True
    )

    parser.add_argument(
        '-reverse',
        action="store",
        dest="reverse_reads",
        nargs="+",
        help="The REVERSE fastq samples that will be used \
        for this run.",
        required=True
    )  # Reverse Short Read Files

    parser.add_argument(
        '-c',
        action="store",
        dest="cores",
        help="Number of cores on which cgap should run.",
        type=int,
        default=cpu_count()
    )  # number of cores

    parser.add_argument(
        '-skip_blast',
        action="store_true",
        help="If present, skip blast and use orig fastqs."
    )

    parser.add_argument(
        '-format_db',
        action="store_true",
        help="If present, format the blast databases."
    )

    args = parser.parse_args()

    return args.refs_path, args.forward_reads, \
    args.reverse_reads, args.cores, args.format_db, args.skip_blast


def main():
    """ runs all the steps in the cgap pipeline. """
    # Setup for cgap run
    cgap.make_paths()

    refs_path, forward_reads, reverse_reads, \
    cores, format_db, skip_blast = cgap_parser()

    fastqs = forward_reads + reverse_reads
    fastas = list(cgap.get_fasta_paths(refs_path))

    # Create small fastqs
    cmd_dict = {
        'format_cmds': [],
        'blast_cmds': [],
        'hit_cmds': [],
        'phylip_cmds': [],
        'cns_cmds': []
    }

    if not skip_blast:
        for fastq in fastqs:

            cmd_dict['format_cmds'].append(fastq)
            cmd_dict['hit_cmds'].append((fastas, fastq))

            for fasta in fastas:
                cmd_dict['blast_cmds'].append((fasta, fastq))

    for fasta in fastas:

        cmd_dict['phylip_cmds'].append((fasta, forward_reads, reverse_reads))

        for fw_rd, rv_rd in cgap.pair_fastqs(forward_reads, reverse_reads):
            cmd_dict['cns_cmds'].append((fasta, fw_rd, rv_rd, skip_blast))

    print("RUNNING CGAP ON {} CORES".format(cores))
    p_max = Pool(cores)

    p_stable = Pool(5) if cores >= 5 else Pool(cores)

    if not skip_blast:
        if format_db:
            print("FORMATTING BLAST DATABASES...")
            p_stable.map(cgap.run_format_cmd, cmd_dict['format_cmds'])

        print("RUNNING BLAST...")
        p_max.map(cgap.run_blast_argslist, cmd_dict['blast_cmds'])

        print("COLLECTING AND BINNING BLAST HITS")
        p_max.map(cgap.collect_hits_argslist, cmd_dict['hit_cmds'])

    print("BUILDING CONSENSUS SEQUENCES")
    p_stable.map(cgap.pipe_consensus_argslist, cmd_dict['cns_cmds'])

    print("BUILDING PHYLIP FILES")
    p_max.map(cgap.build_phylip_records_argslist, cmd_dict['phylip_cmds'])


if __name__ == '__main__':
    main()
