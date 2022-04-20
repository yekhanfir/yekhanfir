# TCR-pMHC structure generation

The pose generation pipeline is composed of 2 consecutive steps: pMHC generation and TCR-pMHC
generation. They are executed as Argo workflows (see `pipeline/argo/pmhc-gen-workfow.yaml` and
`pipeline/argo/tcr-pmhc-gen-workfow.yaml`) one after the other.

## Step 1: pMHC generation (used by `pipeline/argo/pmhc-gen-workfow.yaml` workflow)

The `gen_pmhc_poses.sh` script takes as input:

- An allele, e.g `A0101`
- A peptide, e.g `ILDFGLAKL`
- A initial pMHC PDB, e.g `/mnt/data/ig-dataset/artefacts/pmhc/A1101.ASMLIKALW.model00_0001.pdb`
- A flag, e.g 2

The output files respects the following convention:

```
<INIT_PDB_STEM>_<PEPTIDE>_<FLAG>_{min,relax}.pdb.gz
```

Example:

```
C0304.ATAVAQLLW.model00_0001_AAAFTGLAL_2_relax.pdb.gz
```

## Step 2: TCR-pMHC generation (used by `pipeline/argo/tcr-pmhc-gen-workfow.yaml` workflow)

The `gen_tcr_pmhc_poses.sh` script takes as input:

- A pMHC PDB, e.g
  `/mnt/data/ig-dataset/generated_pmhc/C0304.ATAVAQLLW.model00_0001_AAAFTGLAL_2_relax.pdb.gz`
- A TCR PDB, e.g `/mnt/data/ig-dataset/artefacts/tcr/tcr-CAAGGSQGNLIF-CASSIRSSYEQYF.pdb`
- A template PDB, e.g `/mnt/data/ig-dataset/artefacts/template/6DKP.rechained.pdb`

The output file respects the following convention:

```
<INIT_PDB_STEM>_<PEPTIDE>_<FLAG>_{min,relax}_<TCR_STEM>_<TEMPLATE_STEM>.pdb.gz
```

Example:

```
C0304.ATAVAQLLW.model00_0001_AAAFTGLAL_2_relax_tcr-CAAADSNYQLIW-CASSEMFLSGTGQEAFF_6DKP.rechained.pdb.gz
```

![Argo workflow](argo_workflow.png)

## Run pipeline in parallel

To make things more convenient, we added 2 scripts `gen_pmhc_poses_parallel.sh` and
`gen_tcr_pmhc_poses_parallel.sh` for generating pMCHs and TCR-pMHCs respectively, in parallel on a
multi-cpus machine.

The `gen_pmhc_poses_parallel.sh` script takes as input:

- A CSV file, as generated by `biondeep_ig.data_gen.ig.data_gen.generate_pmhc_dataset.py`,
  containing in each entry a pMHC template filename, a flag number and an allele-peptide pair to be
  generated.
- An output directory where all the generated pMHCs and score files will be generated.

The `gen_tcr_pmhc_poses_parallel.sh` script takes as input:

- A CSV file, as generated by `biondeep_ig.data_gen.ig.data_gen.generate_tcr_pmhc_dataset.py`,
  containing in each entry a generated pMHC filename, a TCR filename and a TCR-pMHC template
  filename.
- An output directory where all the generated TCR-pMHCs and score files will be generated.

Both scripts make use of [parallel](https://www.gnu.org/software/parallel/man.html), a Linux program
that executes a list of shell commands in parallel using all the available cpus.