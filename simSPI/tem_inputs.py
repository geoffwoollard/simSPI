"""Help format TEM Simulator input parameters."""

import logging
import random
import string
from pathlib import Path

import numpy as np
import yaml


def populate_tem_input_parameter_dict(
    input_params_file,
    mrc_file,
    pdb_file,
    crd_file,
    log_file,
    defocus_file,
    dose=None,
    noise=None,
):
    """Return parameter dictionary with settings for simulation.

    Parameters
    ----------
    input_params_file : str
        Path to the .yml file with the parameters
    mrc_file : str
        Micrograph file
    pdb_file : str
        PDB file of sample
    crd_file : str
        Coordinates of the sample copies
    log_file : str
        Log file for the run
    defocus_file : str
        Defocus File to store defocus distribution
    dose : int
        If present, overrides beam_parameters[electron_dose]
    noise : str
        'yes' or 'no'. If present, overrides detector_params[noise]

    YAML file entries:
    ------------------
    *** molecular_model ***
    - voxel_size_nm                : The size of voxels in the particle map in nm.
    - particle_name                : Name of the particle. Not very important.
    - particle_mrcout [OPTIONAL]   : if present, volume map of sample is written.

    *** specimen_grid_params ***
    - hole_diameter_nm             : diameter in nm
    - hole_thickness_center_nm     : thickness at center in nm
    - hole_thickness_edge_nm       : thickness at edge in nm.
    - particle_slice_pad [OPTIONAL]: pad surrounding sliced particles from micrograph

    *** beam_parameters ***
    - voltage_kv                   : voltage in kV
    - energy_spread_v              : energy spread in V
    - electron_dose_e_per_nm2      : dose per image in e/nm**2
    - electron_dose_std_e_per_nm2  : standard deviation of dose per image

    *** optics_parameters ***
    - magnification                : magnification (81000; 105000; 130000)
    - spherical_aberration_mm      : spherical aberration in mm
    - chromatic_aberration_mm      : chromatic aberration in mm
    - aperture_diameter_um         : diam in um of aperture in back focal plane (50-100)
    - focal_length_mm              : focal length in mm of primary lens
    - aperture_angle_mrad          : aperture angle in mrad of the beam furnished by
                                         the condenser lens
    - defocus_um [OPTIONAL]        : nominal defocus value in um
    - defocus_syst_error_um       : standard deviation of a systematic error
                                         added to the nominal defocus, measured
                                         in um. Same error is added to the defocus
                                         of every image.
    - defocus_nonsyst_error_um     : standard deviation of a nonsystematic error
                                         added to the nominal defocus and the
                                         systematic error, measured in um. A new
                                         value of error is computed for every image.
    - optics_defocusout [OPTIONAL] : if present, defocus values written to file.

    *** detector_parameters ***
    - detector_nx_px               : number of pixels on detector along x axis
    - detector_ny_px               : number of pixels on detector along y axis
    - detector_pixel_size_um       : physical pixel size in um
    - average_gain_count_per_electron : detector gain: avg number of counts per electron
    - noise                        : quantized electron waves result in noise
    - detector_q_efficiency        : detector quantum efficiency
    - mtf_params                   : list of 5 MTF parameters

    *** geometry ***
    - n_samples : number of images of the sample

    *** ctf ***
    - distribution_type [OPTIONAL] : type of distribution. Overrides defocus_um
                                        parameter if present.

    - distribution_parameters [OPTIONAL] : distribution parameters. Required if
                                                distribution_type is present.
    *** noise ***
    - signal_to_noise [OPTIONAL]   : signal-to-noise ratio for gaussian white noise.
    - signal_to_noise_db [OPTIONAL] : signal-to-noise ratio in decibels.

    *** miscellaneous ***
    - seed [OPTIONAL]              : seed for the run. If not present, random.

    Raises
    ------
    TypeError
        Raised when path has invalid extension.
    """
    parameters = None
    log = logging.getLogger()

    suffix = Path(input_params_file).suffix
    allowed_types = [".yml", ".yaml"]
    if suffix.lower() not in allowed_types:
        log.error(
            f"`File Path : {input_params_file} must be of type(s) {allowed_types} "
        )
        raise TypeError()

    with open(input_params_file, "r") as f:
        parameters = yaml.safe_load(f)

    dic = {"simulation": {}}
    try:
        dic["simulation"]["seed"] = parameters["miscellaneous"]["seed"]
    except KeyError:
        random.seed()
        dic["simulation"]["seed"] = random.randint(0, int(1e10))

    dic["simulation"]["log_file"] = log_file

    dic["noise"] = {}
    try:
        dic["noise"]["signal_to_noise"] = parameters["noise_parameters"][
            "signal_to_noise"
        ]
    except KeyError:
        pass

    try:
        dic["noise"]["signal_to_noise_db"] = parameters["noise_parameters"][
            "signal_to_noise_db"
        ]
    except KeyError:
        pass

    dic["simulation"]["log_file"] = log_file
    dic["sample"] = {}
    dic["sample"]["diameter"] = parameters["specimen_grid_params"]["hole_diameter_nm"]
    dic["sample"]["thickness_center"] = parameters["specimen_grid_params"][
        "hole_thickness_center_nm"
    ]
    dic["sample"]["thickness_edge"] = parameters["specimen_grid_params"][
        "hole_thickness_edge_nm"
    ]
    dic["particle"] = {}
    dic["particle"]["name"] = parameters["molecular_model"]["particle_name"]
    dic["particle"]["voxel_size"] = parameters["molecular_model"]["voxel_size_nm"]
    dic["particle"]["pdb_file"] = pdb_file

    if "particle_mrcout" in parameters["molecular_model"]:
        key = parameters["molecular_model"]["particle_mrcout"].split(".mrc")[0]
        dic["particle"]["map_file_re_out"] = key + "_real.mrc"
        dic["particle"]["map_file_im_out"] = key + "_imag.mrc"
    else:
        dic["particle"]["map_file_re_out"] = None

    dic["particleset"] = {}
    dic["particleset"]["name"] = parameters["molecular_model"]["particle_name"]
    dic["particleset"]["crd_file"] = crd_file

    dic["beam"] = {}
    dic["beam"]["voltage"] = parameters["beam_parameters"]["voltage_kv"]
    dic["beam"]["spread"] = parameters["beam_parameters"]["energy_spread_v"]

    if dose is not None:
        dic["beam"]["dose_per_im"] = dose
    else:
        dic["beam"]["dose_per_im"] = parameters["beam_parameters"][
            "electron_dose_e_per_nm2"
        ]

    dic["beam"]["dose_sd"] = parameters["beam_parameters"][
        "electron_dose_std_e_per_nm2"
    ]

    dic["optics"] = {}
    dic["optics"]["magnification"] = parameters["optics_parameters"]["magnification"]
    dic["optics"]["cs"] = parameters["optics_parameters"]["spherical_aberration_mm"]
    dic["optics"]["cc"] = parameters["optics_parameters"]["chromatic_aberration_mm"]
    dic["optics"]["aperture"] = parameters["optics_parameters"]["aperture_diameter_um"]
    dic["optics"]["focal_length"] = parameters["optics_parameters"]["focal_length_mm"]
    dic["optics"]["cond_ap_angle"] = parameters["optics_parameters"][
        "aperture_angle_mrad"
    ]

    if "optics_defocusout" in parameters["optics_parameters"]:
        dic["optics"]["defocus_file_out"] = parameters["optics_parameters"][
            "optics_defocusout"
        ]
    else:
        dic["optics"]["defocus_file_out"] = None

    dic["detector"] = {}

    if "defocus_um" in parameters["optics_parameters"]:
        dic["optics"]["defocus_nominal"] = parameters["optics_parameters"]["defocus_um"]
        dic["detector"]["mtf_a"] = parameters["optics_parameters"]["defocus_um"]
    else:
        dic["optics"]["defocus_nominal"] = parameters["detector_parameters"][
            "mtf_params"
        ][0]
        dic["detector"]["mtf_a"] = parameters["detector_parameters"]["mtf_params"][0]

    dic["optics"]["defocus_syst_error"] = parameters["optics_parameters"][
        "defocus_syst_error_um"
    ]
    dic["optics"]["defocus_nonsyst_error"] = parameters["optics_parameters"][
        "defocus_nonsyst_error_um"
    ]

    dic["detector"]["det_pix_x"] = parameters["detector_parameters"]["detector_nx_px"]
    dic["detector"]["det_pix_y"] = parameters["detector_parameters"]["detector_ny_px"]
    dic["detector"]["pixel_size"] = parameters["detector_parameters"][
        "detector_pixel_size_um"
    ]
    dic["detector"]["gain"] = parameters["detector_parameters"][
        "average_gain_count_per_electron"
    ]

    if noise is not None:
        dic["detector"]["use_quantization"] = noise
    else:
        dic["detector"]["use_quantization"] = parameters["detector_parameters"]["noise"]

    dic["detector"]["dqe"] = parameters["detector_parameters"]["detector_q_efficiency"]
    dic["detector"]["mtf_b"] = parameters["detector_parameters"]["mtf_params"][1]
    dic["detector"]["mtf_c"] = parameters["detector_parameters"]["mtf_params"][2]
    dic["detector"]["mtf_alpha"] = parameters["detector_parameters"]["mtf_params"][3]
    dic["detector"]["mtf_beta"] = parameters["detector_parameters"]["mtf_params"][4]
    dic["detector"]["image_file_out"] = mrc_file

    dic["geometry"] = {}
    dic["geometry"]["n_tilts"] = parameters["geometry_parameters"]["n_samples"]

    try:
        dic["ctf"] = {}
        dic["ctf"]["distribution_type"] = parameters["ctf_parameters"][
            "distribution_type"
        ]
        dic["ctf"]["distribution_parameters"] = parameters["ctf_parameters"][
            "distribution_parameters"
        ]
        dic["optics"]["gen_defocus"] = "no"
        dic["optics"]["defocus_file_in"] = defocus_file
    except KeyError:
        log.warning("ctf_parameters not found/invalid. Using constant defocus.")
        dic["optics"]["gen_defocus"] = "yes"
        dic["optics"]["defocus_file_in"] = None

    return dic


def starfile_append_tem_simulator_data(
    data_list,
    rotation,
    contrast_transfer_function,
    projection_shift,
    iterations,
    config,
):
    """Append the data list with the parameters of the simulator.

    Parameters
    ----------
    data_list: list
        list containing the metadata of the projection chunks.
        Mutated by this method.
    rotation: dict of type str to {tensor}
        Dictionary of rotation parameters for a projection chunk
    contrast_transfer_function: dict of type str to {tensor}
        Dictionary of Contrast Transfer Function (CTF) parameters
         for a projection chunk
    projection_shift: dict of type str to {tensor}
        Dictionary of shift parameters for a projection chunk
    iterations: int
        iteration number of the loop. Used in naming the mrcs file.
    config: class
         class containing parameters of the dataset generator.

    Returns
    -------
    data_list: list
        list containing the metadata of the projection chunks.
        This list is then used to save the starfile.
    """
    image_name = [
        str(idx).zfill(3) + "@" + str(iterations).zfill(4) + ".mrcs"
        for idx in range(config.batch_size)
    ]

    for num in range(config.batch_size):
        list_var = [
            image_name[num],
            rotation["relion_angle_rot"][num].item(),
            rotation["relion_angle_tilt"][num].item(),
            rotation["relion_angle_psi"][num].item(),
        ]
        if projection_shift:
            list_var += [
                projection_shift["shift_x"][num].item(),
                projection_shift["shift_y"][num].item(),
            ]
        if contrast_transfer_function:
            list_var += [
                1e4 * contrast_transfer_function["defocus_u"][num].item(),
                1e4 * contrast_transfer_function["defocus_v"][num].item(),
                np.radians(contrast_transfer_function["defocus_angle"][num].item()),
            ]

        list_var += [
            config.kv,
            config.pixel_size,
            config.cs,
            config.amplitude_contrast,
            config.b_factor,
        ]
        data_list.append(list_var)
    return data_list


def write_tem_defocus_file_from_distribution(path: str, distribution: list):
    """Write defocus distribution into tabular formatted file.

    Parameters
    ----------
    path : str
        File path to defocus file.
    distribution : list
        Defocus distribution.

    Raises
    ------
    TypeError
        Raised when path has invalid extension.
    """
    log = logging.getLogger()
    suffix = Path(path).suffix
    allowed_types = [".txt"]

    if suffix.lower() not in allowed_types:
        log.error(f"`File Path : {path} must be of type(s) {allowed_types} ")
        raise TypeError()

    with open(path, "w") as inp:
        inp.write("# File created by TEM-simulator, version 1.3.\n")
        inp.write(f"{len(distribution)} 1\n")
        for sample in distribution:
            inp.write(f"{sample}\n")


def write_tem_inputs_to_inp_file(path, tem_inputs):
    """Write tem simulator inputs to input .inp file.

    Parameters
    ----------
    path : str
        Relative path to input file.
    tem_inputs : dict
        Dictionary containing parameters to write.

    Raises
    ------
    TypeError
        Raised when path has invalid extension.
    """
    log = logging.getLogger()
    suffix = Path(path).suffix
    allowed_types = [".inp"]

    if suffix.lower() not in allowed_types:
        log.error(f"`File Path : {path} must be of type(s) {allowed_types} ")
        raise TypeError()
    with open(path, "w") as inp:
        inp.write(
            "=== simulation ===\n"
            "generate_micrographs = yes\n"
            "rand_seed = {0[seed]}\n"
            "log_file = {0[log_file]}\n".format(tem_inputs["simulation"])
        )
        inp.write(
            "=== sample ===\n"
            "diameter = {0[diameter]:d}\n"
            "thickness_edge = {0[thickness_edge]:d}\n"
            "thickness_center = {0[thickness_center]:d}\n".format(tem_inputs["sample"])
        )
        inp.write(
            "=== particle {0[name]} ===\n"
            "source = pdb\n"
            "voxel_size = {0[voxel_size]}\n"
            "pdb_file_in = {0[pdb_file]}\n".format(tem_inputs["particle"])
        )
        if tem_inputs["particle"]["map_file_re_out"] is not None:
            inp.write(
                "map_file_re_out = {0[map_file_re_out]}\n"
                "map_file_im_out = {0[map_file_im_out]}\n".format(
                    tem_inputs["particle"]
                )
            )
        inp.write(
            "=== particleset ===\n"
            "particle_type = {0[name]}\n"
            "particle_coords = file\n"
            "coord_file_in = {0[crd_file]}\n".format(tem_inputs["particleset"])
        )
        inp.write(
            "=== geometry ===\n"
            "gen_tilt_data = yes\n"
            "tilt_axis = 0\n"
            "ntilts = {0[n_tilts]}\n"
            "theta_start = 0\n"
            "theta_incr = 0\n"
            "geom_errors = none\n".format(tem_inputs["geometry"])
        )
        inp.write(
            "=== electronbeam ===\n"
            "acc_voltage = {0[voltage]}\n"
            "energy_spread = {0[spread]}\n"
            "gen_dose = yes\n"
            "dose_per_im = {0[dose_per_im]}\n"
            "dose_sd = {0[dose_sd]}\n".format(tem_inputs["beam"])
        )
        inp.write(
            "=== optics ===\n"
            "magnification = {0[magnification]}\n"
            "cs = {0[cs]}\n"
            "cc = {0[cc]}\n"
            "aperture = {0[aperture]}\n"
            "focal_length = {0[focal_length]}\n"
            "cond_ap_angle = {0[cond_ap_angle]}\n"
            "gen_defocus = {0[gen_defocus]}\n"
            "defocus_nominal = {0[defocus_nominal]}\n"
            "defocus_syst_error = {0[defocus_syst_error]}\n"
            "defocus_syst_error = {0[defocus_nonsyst_error]}\n".format(
                tem_inputs["optics"]
            )
        )
        if tem_inputs["optics"]["defocus_file_out"] is not None:
            inp.write(
                "defocus_file_out = {0[defocus_file_out]}\n".format(
                    tem_inputs["optics"]
                )
            )
        if tem_inputs["optics"]["defocus_file_in"] is not None:
            inp.write(
                "defocus_file_in = {0[defocus_file_in]}\n".format(tem_inputs["optics"])
            )
        inp.write(
            "=== detector ===\n"
            "det_pix_x = {0[det_pix_x]}\n"
            "det_pix_y = {0[det_pix_y]}\n"
            "pixel_size = {0[pixel_size]}\n"
            "gain = {0[gain]}\n"
            "use_quantization = {0[use_quantization]}\n"
            "dqe = {0[dqe]}\n"
            "mtf_a = {0[mtf_a]}\n"
            "mtf_b = {0[mtf_b]}\n"
            "mtf_c = {0[mtf_c]}\n"
            "mtf_alpha = {0[mtf_alpha]}\n"
            "mtf_beta = {0[mtf_beta]}\n"
            "image_file_out = {0[image_file_out]}\n".format(tem_inputs["detector"])
        )


def retrieve_rotation_metadata(path):
    """Retrieve particle rotation data from pre-generated simulator crd file.

    Parameters
    ----------
    path : str
        String specifying path to crd file generated during simulation.

    Returns
    -------
    rotation_metadata : array-like, shape=[..., 3]
        N x 3 matrix representing the rotation angles , phi, theta, psi, of
        each particle in stack.

    Raises
    ------
    TypeError
        Raised when path has invalid extension.
    """
    rotation_metadata = []
    lines = []

    log = logging.getLogger()
    suffix = Path(path).suffix
    allowed_types = [".txt"]

    if suffix.lower() not in allowed_types:
        log.error(f"`File Path : {path} must be of type(s) {allowed_types} ")
        raise TypeError()
    with open(path) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if i >= 4:
            rotation_metadata.append([float(x) for x in line.split()[:]])

    return rotation_metadata  # TOD


def generate_path_dict(
    pdb_file, metadata_params_file, output_dir=None, mrc_keyword=None, **kwargs
):
    """Return dict containing path_config paths and output files as strings.

    Parameters
    ----------
    pdb_file : str
        Relative path to the pdb file
    metadata_params_file : str
        Relative path to metadata params file
    output_dir : str, (default = None)
        Relative path to output directory
    mrc_keyword : str, (default = None)
        user-specified keyword appended to output files
    kwargs
        compatibility for arbitrary extra parameters.

    Returns
    -------
    path_dict : dict of type str to str
        Dict of file paths that includes keys:
        pdb_file
            relative path to pdb input file
        metadata_params_file
            relative path to metadata_params file
        crd_file
            relative path to desired output crd file
        h5_file
            relative path to desired output h5 file
        inp_file
            relative path to desired output inp file
        mrc_file
            relative path to desired output mrc file
        log_file
            relative path to desired output log file
        defocus_file
            relative path to desired output defocus parameter file
        star_file
            relative poth to desured output star file
    """
    path_dict = {}

    if output_dir is None:
        output_dir = str(Path(pdb_file).parent)

    pdb_keyword = Path(pdb_file).stem

    if mrc_keyword is None:
        mrc_keyword = "_" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )

    path_dict["pdb_file"] = str(Path(pdb_file))
    path_dict["metadata_params_file"] = str(Path(metadata_params_file))
    path_dict["crd_file"] = str(Path(output_dir, pdb_keyword + mrc_keyword + ".txt"))
    path_dict["mrc_file"] = str(Path(output_dir, pdb_keyword + mrc_keyword + ".mrc"))
    path_dict["log_file"] = str(Path(output_dir, pdb_keyword + mrc_keyword + ".log"))
    path_dict["inp_file"] = str(Path(output_dir, pdb_keyword + mrc_keyword + ".inp"))
    path_dict["h5_file"] = str(Path(output_dir, pdb_keyword + mrc_keyword + ".h5"))
    path_dict["star_file"] = str(Path(output_dir, pdb_keyword + mrc_keyword + ".star"))
    path_dict["defocus_file"] = str(
        Path(output_dir, pdb_keyword + mrc_keyword + "_defocus" + ".txt")
    )

    return path_dict


def classify_input_config(raw_params):
    """Take dictionary of unordered parameters and groups them into lists.

    Parameters
    ----------
    raw_params : dict of type str to {str,bool,int}
        Dictionary of simulator parameters
    Returns
    -------
    classified_params : dict of type str to {str,bool,int,list}
        Dictionary of grouped parameters
    """
    sim_params_structure = {
        "molecular_model": ["voxel_size_nm", "particle_name", "particle_mrcout"],
        "specimen_grid_params": [
            "hole_diameter_nm",
            "hole_thickness_center_nm",
            "hole_thickness_edge_nm",
            "particle_slice_pad",
        ],
        "beam_parameters": [
            "voltage_kv",
            "energy_spread_v",
            "electron_dose_e_nm2",
            "electron_dose_std_e_per_nm2",
        ],
        "optics_parameters": [
            "magnification",
            "spherical_aberration_mm",
            "chromatic_aberration_mm",
            "aperture_diameter_um",
            "focal_length_mm",
            "aperture_angle_mrad",
            "defocus_um",
            "defocus_syst_error_um",
            "defocus_nonsyst_error_um",
            "optics_defocusout",
        ],
        "detector_parameters": [
            "detector_nx_px",
            "detector_ny_px",
            "detector_pixel_size_um",
            "average_gain_count_per_electron",
            "noise",
            "detector_q_efficiency",
            "mtf_params",
        ],
    }

    classified_sim_params = {}

    for param_type, param_order in sim_params_structure.items():
        if param_type != "detector_parameters":
            classified_sim_params[param_type] = [
                raw_params[param_type].get(key) for key in param_order
            ]
        elif param_type == "detector_parameters":
            ordered_params = [raw_params[param_type].get(key) for key in param_order]
            flattened_params = []

            for i in range(6):
                flattened_params.append(ordered_params[i])
            for i in range(5):
                flattened_params.append(ordered_params[6][i])

            classified_sim_params[param_type] = flattened_params

    return classified_sim_params


def get_config_from_yaml(config_yaml):
    """Create dictionary with parameters from YAML file and groups them into lists.

    Parameters
    ----------
    config_yaml : str
        Relative path to YAML file containing parameters for TEM Simulator
    Returns
    -------
    classified_params : dict
        Dictionary containing grouped parameters for TEM Simulator, with keys:
            seed : str maps to int
                Seed for TEM Simulator
            particle_mrcout : str maps to bool
                Flag for optional volume map of sample
            sample_dimensions : str maps to
                List containing the specimen grid parameters
            beam_params : str maps to list
                List containing the beam parameters
            detector_params : str maps to list
                List containing the detector parameters
            optics_params : str maps to list
                List containing the optic parameters
    Raises
    ------
    TypeError
        Raised when config_yaml has invalid extension.
    """
    log = logging.getLogger()
    suffix = Path(config_yaml).suffix
    allowed_types = [".yaml", ".yml"]

    if suffix.lower() not in allowed_types:
        log.error(f"`File Path : {config_yaml} must be of type(s) {allowed_types} ")
        raise TypeError()

    with open(config_yaml, "r") as stream:
        raw_params = yaml.safe_load(stream)

    classified_params = classify_input_config(raw_params)

    return classified_params
