from dataclasses import dataclass


@dataclass
class DockingResult:
    """
    Data container for molecular docking results.

    Stores paths to output files generated during a docking operation
    and provides a property to check if the docking was successful.
    """

    receptor_file: str = None
    pos_file: str = None
    ligand_file: str = None
    log_file: str = None

    @property
    def success(self) -> bool:
        """
        Indicates whether the docking was successful.
        """
        return (
            self.receptor_file is not None
            and self.pos_file is not None
            and self.ligand_file is not None
        )
