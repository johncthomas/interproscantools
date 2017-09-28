#!/usr/bin/env python3
__author__ = 'https://github.com/johncthomas'

from Bio import SeqIO
import os, sys, argparse

from subprocess import Popen
import time
#import xml.sax


"""see iprscan_from_fasta.iprscan.__doc__"""

def iprscan(fasta_file_path, out_dir, email, file_name_prefix ='',
            use_fasta_descriptions = False, auto_numbering = True,
            single_results_format = False,
            max_concurrent_jobs = 20, polling_time = 10,
            record_start_stop = None,
            __filenametest = False):
    """
    Takes a FASTA file path, sends the sequences contained
    within to IPRScan, results of which are then saved to
    the harddrive.

    Args:
    fasta_file_path:
        The full path to the fasta file

    out_dir:
        The directory where the IPR results will be saved.

    email:
        Your email.

    file_name_prefix (Default: ''):
        Optional prefix given to all results files generated.
        (See note below)

    use_fasta_descriptions (Default: False):
        If True the FASTA record descriptions/titles are used in the
        generated results file names. If you pass a function it will
        be given the FASTA desc as an arg and the product as the file
        name.

    single_results_format (Default: False):
        By default IPRScan returns a bunch of formats. You can specify
        a single format here (e.g 'svg'). If you want more than one
        it's probably easier to get them all and delete the ones you
        don't want. Other functions I've written use XML results.
        SVG are pretty.

    max_concurrent_jobs (Default: 20; max: 20):
        Maximum jobs sent to IPRScan concurrently.

    polling_time (Default: 10):
        How often the status of running jobs are checked, in seconds.

    *Note on file names*:
    All generated files are numbered so if you supply a prefix and
    use_fasta_descriptions is True the files will look something
    like this:
        prefix_0001_-_fasta_record_desciption.svg.svg
    If both those args are False then the files will just be numbered:
        0001.svg.svg
    Requires either autonumbering or usefastadescriptions

    """

    # Goes through the fasta getting AA sequences and constructing the eventual filenames
    # based on the arguments given.
    # Subprocess objects are created using Popen that run IPRScan.py from the command line
    # with the appropriate arguments. IPRScan.py sends the data to the
    # InterPro server. Subprocesses generated are put
    # into current_jobs and periodically polled to
    # check if they've finished.


    #check we have filenames
    assert auto_numbering or use_fasta_descriptions

    # Clean up arguments
    # EBI ask that you don't send more than 20 jobs at once.
    if max_concurrent_jobs > 20:
        max_concurrent_jobs = 20


    # Check the results directory exists, prompt creation if it doesnt
    out_dir = os.path.abspath(out_dir)
    if not os.path.isdir(out_dir):
        print('Results destination', out_dir, 'does not exist.')
        response = input('Create results directory/folder? (Y/n)')
        if not response or response in 'Yy':
            os.mkdir(out_dir)
        else:
            return 0

    # Check for potential results files and warn about overwriting
    filesinout = [f for f in os.listdir(out_dir) if ('.svg' in f or '.xml' in f) and file_name_prefix in f]
    if filesinout:
        print('Possible results files found in results directory, e.g.:')
        for f in filesinout[:5]:
            print(f)
        response = input('Files may be overwritten without further warning. Is that okay? (Y/n)')
        if not response or response in 'Yy':
            pass
        else:
            return 0


    # count records, set r_s_s if required, inform user of record count
    fasta_file_path = os.path.abspath(fasta_file_path)
    record_count = 0
    with open(fasta_file_path) as f:
        for line in f.readlines():
            #print(line)
            if line[0] == '>':
                record_count+=1
    count_figures = len(str(record_count))

    if record_start_stop is not None:
        if record_start_stop[1] is None:
            record_start_stop = record_start_stop[0], record_count


    print('FastA file contains', record_count, 'records.')

    # Format of the command used to run IPRScan.py
    if single_results_format:
        iprscan_s = 'python IPRscan.py --email {} --outformat {} --sequence {} --outfile "{}"'.format(
            email, single_results_format, '{}', '{}'
        )
    else:
        iprscan_s = 'python IPRscan.py --email {} --sequence {} --outfile "{}"'.format(
            email, '{}', '{}'
        )

    # Format string for the results file name
    file_name_template = file_name_prefix+'_{}{}' if file_name_prefix else '{}{}'

    # Go through the fasta records submitting jobs
    fasta_records = SeqIO.parse(fasta_file_path, 'fasta')

    # get job info from FastA. jobs = [(seq, filename), ...]
    jobs = []

    FunctionType = type(lambda x: x)

    for job_count, record in enumerate(fasta_records):
        # Skip records if outside of range defined by record_start_stop (or r_s_s is None)
        if not record_start_stop or record_start_stop[0] <= job_count <= record_start_stop[1]:

            # Get the results file name
            # Add leading zeroes to the number string
            if auto_numbering:
                num_string = '0'*(count_figures-len(str(job_count)))+str(job_count)
            else:
                num_string = ''

            # get the rest of the file name
            if use_fasta_descriptions:
                if type(use_fasta_descriptions) == FunctionType:
                    desc = use_fasta_descriptions(record.description)
                else:
                    desc = record.description
                for banned_char in '<>:"/\\|?*':
                    desc = desc.replace(banned_char, '_')
                if auto_numbering:
                    desc = '_-_' + desc
            else:
                desc = ''

            file_name = file_name_template.format(num_string, desc)
            # add the sequence and filename to the jobs list
            jobs.append((str(record.seq), file_name))

        elif job_count > record_start_stop[1]:
            break
    if __filenametest:
        for j in jobs:
            print(j)
        return 0
    # Function used while polling current_jobs to add a wait
    def poll_wait(job):
        # if new_job == 'test':
        #     return True
        time.sleep(polling_time / max_concurrent_jobs)
        return job.poll()

    # Where  currently running jobs will be stored while
    # waiting for the interpro server
    current_jobs = []
    jobs = iter(jobs)
    done = False

    while not done:
        # subprocess.poll() returns None while waiting for interpro
        current_jobs = [subprocess for subprocess in current_jobs if poll_wait(subprocess) is None]
        while len(current_jobs) < max_concurrent_jobs:
            try:
                seq, file_name = next(jobs)
            except StopIteration:
                done = True
                break
            # Call Popen() with the formated string containing all the args
            job_string = iprscan_s.format( seq, os.path.join(out_dir,file_name) )
            new_job = Popen(job_string)
            #new_job = 'test'
            current_jobs.append(new_job)

            print('# jobs running:', len(current_jobs))
            time.sleep(0.5)

    # All jobs added, keep the python program running, this
    # might be required to get the results from the IPRS server
    # server, or it might not. I dunno but it seems sensible to keep it going.
    finished = False
    while not finished:
        time.sleep(polling_time)
        current_jobs = [subprocess for subprocess in current_jobs if subprocess.poll() is None]
        if not current_jobs:
            finished = True


def run_from_command_line():

    # Get arguments/options from command line, sys.argv
    parser = argparse.ArgumentParser(
        description=
        """Takes a FASTA containing amino acid sequences, sends them to
    IPRScan, results of which are then saved to the harddrive.""",
        formatter_class=argparse.RawDescriptionHelpFormatter, # don't strip newlines from discriptoin/epilog
        epilog=
        """    **Notes on file names**:
    All generated files are numbered so if you supply a prefix and
    use_fasta_descriptions is True the files will look something
    like this:
        prefix_0001_-_Fasta_file_desciption.svg.svg
    If both those args are False then the files will just be numbered:
        0001.svg.svg
        """
    )

    # add parser arguments
    parser.add_argument("fasta_file", help = 'Path to the fasta file.')
    parser.add_argument("out_dir", help = 'The directory where the IPR results will be saved.')
    parser.add_argument("email", help = "Your email, required by EBI so they can get in touch if there's a problem")
    parser.add_argument('-p', '--prefix', metavar="RESULTS-PREFIX", default = '', help =
        "Optional prefix given to all results files generated. \n\
    (See note on filenames below)")
    parser.add_argument('-d', '--use-fasta-descript', action='store_true', help =
        """"Flag to use FastA record descriptions/titles the generated results file names.
        Replaces illegal characters with underscores. When calling this function in Python directly, 
        you can pass a function to process the 
        FastA description.""" )
    parser.add_argument(
        '-n', '--no-numbering',
        dest = 'numbering',
        action = 'store_false',
        help = "Don't number results files."
    )
    parser.add_argument('-f', '--frm', metavar="FROM_RECORD", default = 0, type = int, help =
        'FastA record number from which to start. Useful if a process got interupted.\
        Defaults to the first record.')
    parser.add_argument('-t', '--to', metavar="TO_RECORD", type = int,  help =
        "FastA record number to stop at. Useful for testing. Continues to end of FastA by default.")



    args = parser.parse_args()
    # Check we have filenames
    assert args.use_fasta_descript or args.numbering
    iprscan(
        args.fasta_file,
        args.out_dir,
        args.email,
        file_name_prefix = args.prefix,
        use_fasta_descriptions = args.use_fasta_descript,
        auto_numbering = args.numbering,
        record_start_stop = (args.frm, args.to)
    )

if __name__ == '__main__':
    print(sys.argv)
    run_from_command_line()
#
# if __name__ == '__main__':
#     iprscan(r'D:\Dropbox\PhD\Experiments\Bioinfo\Sequences\test.faa',
#             r'D:\Dropbox\PhD\Experiments\Bioinfo\All E1 IPRScan',
#             'jct513@york.ac.uk', use_fasta_descriptions=True,
#             auto_numbering=True,
#             )
