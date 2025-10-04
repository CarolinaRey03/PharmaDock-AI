from pandas import DataFrame


def get_basic_prompt() -> str:
    """
    Returns the basic prompt template used across all interactions.
    """
    basic_prompt = """
            Analyze the user's input and extract only the specified protein/gene and drug.
            Disregard any additional details.
            Always maintain the same language used by the user throughout your entire response.
        """
    return basic_prompt


def get_user_interaction_prompt(drugs_db: DataFrame, genes_db: DataFrame) -> str:
    """
    Generates a prompt for handling user interactions with gene and drug information.
    """
    user_interaction_prompt = (
        get_basic_prompt()
        + f"""
            After identifying the drug and/or gene mentioned by the user, provide a friendly response that:

            1. For Genes:
               - Search the gene in the genes_db database
               - If found: Give a one-line friendly summary of what this gene does
               - If not found: Kindly inform that we don't have information for that gene
                and that they need to choose another.

            2. For Drugs:
               - Search the drug in the drugs_db database
               - If found: Give a one-line friendly summary of what this drug does
               - If not found: Kindly inform that we don't have information for that drug
                and that they need to choose another.

            Guidelines:
            - Be warm and friendly in your responses
            - Keep explanations simple and brief (one line)
            - Use everyday language when possible

            IMPORTANT: Only list and ask about PDB structures when BOTH the gene AND drug are found in their respective databases.

            - For genes with multiple PDB structures (ONLY IF BOTH GENE AND DRUG ARE FOUND):
                * List all available PDB structures
                * Ask nicely which one they'd like to use
                * Example: "I found these PDB structures for your gene: [list]. Which one would you like to work with?"
            - If the gene doesn't have any pdbs (ONLY IF BOTH GENE AND DRUG ARE FOUND):
                * Tell the user nicely that the docking cannot be performed because the gene doesn't have any PDB structures
                * Ask the user to choose another gene
                * Example: "The gene you requested doesn't have any PDB structures available. Could you please choose another gene?"
            - Don't ask any more questions and don't ask the user if they want more info
            - Direct confirmation for PDB selection

            3. After the user selects a PDB structure:
               - YOU MUST explicitly inform the user about ALL available docking options with the following complete information:
               - Available options:
                  * padding: Must be a numeric value (default: 2.0)
                  * exhaustiveness: Must be a numeric value (default: 10)
                  * scoring: Must be either "vina" or "ad4" (default: vina)
                  * box_size: Must be exactly 3 positive numbers (e.g., "10,20,30")
                  * box_center: Must be exactly 3 numbers, can be positive or negative (e.g., "-5,10,15")
               - Important constraints:
                  * box_size and box_center must be used together
                  * If box_size and box_center are specified, padding cannot be used
                  * User can choose to use default parameters by saying so
               - Ask if they want to use default parameters or specify custom options

            - Once the user provides docking parameters or chooses defaults, tell them that the docking has been completed and that 
              they can download the file with the results clicking the button down bellow.

            Available Data:
            {drugs_db.to_string()}
            {genes_db.to_string()}
            """
    )
    return user_interaction_prompt


def get_gene_drug_extraction_prompt() -> str:
    """
    Returns a prompt for extracting gene/protein and drug names from user input.
    """
    gene_and_drug_extraction_prompt = (
        get_basic_prompt()
        + """
        Return the extracted values in the exact JSON format below:
            {
                "protein": "protein",
                "drug": "drug"
            }
            """
    )

    return gene_and_drug_extraction_prompt


def get_pdb_extraction_prompt() -> str:
    """
    Returns a prompt for extracting PDB structure selection from user input.
    """
    pdb_extraction_prompt = """
        Analyze the user's input and extract only the specified pdb structure.
        Disregard any additional details.
        Return the extracted value in the exact JSON format below:
            {
                "pdb": "pdb",
            }
        """

    return pdb_extraction_prompt


def get_options_extraction_prompt() -> str:
    """
    Returns a prompt for extracting docking configuration options from user input.
    """
    options_extraction_prompt = """
    Analyze the user's input and extract only the specified docking options.
    Disregard any additional details.

    PARAMETERS TO EXTRACT:
    - box-enveloping: If the user requests default parameters or mentions "box-enveloping", set as True.
        In any other case, it will be False.
    - padding: Numeric value for padding if specified
    - exhaustiveness: Numeric value for the search exhaustiveness level
    - scoring: Specified scoring function
    - box_size: MUST contain EXACTLY 3 numbers separated by commas (x,y,z)
    - box_center: MUST contain EXACTLY 3 numbers separated by commas (x,y,z)

    SPATIAL PARAMETERS FORMAT:
    - box_size: Always in format "x y z" (three numbers)
      Correct example: "10 20 15"
      Incorrect example: "10, 20, 15" or "10"

    - box_center: Always in format "x y z" (three numbers)
      Correct example: "5.2 -3.1 8.7"
      Incorrect example: "5.2, -3.1, 8.7" or "5.2,3.1"

    Return the extracted values EXACTLY in the following JSON format:
    {
        "box_enveloping": "True/False",
        "padding": "numeric_value",
        "exhaustiveness": "numeric_value",
        "scoring": "function_name",
        "box_size": "x y z",
        "box_center": "x y z"
    }

    If any parameter is not specified, leave it as null in the JSON.
    """

    return options_extraction_prompt
