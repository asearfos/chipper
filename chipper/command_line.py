import os
import time
from chipper.log import get_logger
from chipper.analysis import Song, output_bout_data

log = get_logger(__file__)


def run_analysis(input_directory, user_noise_thresh, user_syll_sim_thresh,
                 out_path=None):
    """

    Parameters
    ----------
    input_directory : str
    user_noise_thresh : int
    user_syll_sim_thresh : int
    out_path : str

    """

    files = [i for i in os.listdir(os.path.join(input_directory))
             if i.endswith('.gzip')]

    if not len(files):
        log.debug("No gzipped files in {}".format(input_directory))
        raise Exception("No gzipped files in {}".format(input_directory))

    if out_path is None:
        suffix = "AnalysisOutput_" + time.strftime("%Y%m%d_T%H%M%S")
        out_path = os.path.join(input_directory, suffix)

    file_names = [os.path.join(input_directory, i) for i in files]

    final_output = []
    n_files = len(files)
    errors = ''
    for i in range(n_files):
        f_name = file_names[i]
        log.info("{} of {} complete".format(i, n_files))
        try:
            log.info("{} of {} complete".format(i, n_files))
            output = Song(f_name, user_noise_thresh,
                          user_syll_sim_thresh).run_analysis()
            output['f_name'] = f_name
            final_output.append(output)
        except Exception as e:
            errors += "WARNING : Skipped file {0}\n{1}\n".format(f_name,
                                                                  e)
            log.info(errors)
    # write errors to log file
    error_file = "{}_{}".format(out_path, "error_log")
    if os.path.exists(error_file):
        action = 'a'
    else:
        action = 'w'
    with open(error_file, action) as f:
        f.write(errors)
    log.info("{0} of {0} complete".format(n_files))
    output_bout_data(out_path, final_output)


