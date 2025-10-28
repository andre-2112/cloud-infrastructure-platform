# Tasks 

## Task 1 - Read and Understand.

    1.1 - Understand latest version of the Architecture.

        - Multi-Stack-Architecture-2.3.md
        - Use it as a base reference.

    1.2 - Undestand the existing stacks under ./aws/build/<stack>/v2/

        - ./aws/build/<stack>/v2/docs
        - ./aws/build/<stack>/v2/resources

    1.3 - Read and understand additional contextual documents:

        - ./admin/v2/docs/Prompt-11 - Pre-Implementation - Responses.md

        OBSERVATION: 
            - This file used to be ""Answers_Pre-Implementation.2.3.md", but it has been renamed.
            - This document uses the new filename ("Prompt-11 - Pre-Implementation - Responses.md").

    1.4 - Read this whole document.

        - Understand all of the tasks below, individually and as a whole.
  
    IMPORTANT: Start planning ONLY after all tasks are read.

## Task 2 - Adjust the latest architecture (Multi-Stack-Architecture-2.3), according to the changes below:

    Systematically, adjust the latest architecture, according to the changes below:

    2.1 - All references to the CLI tool name "multi-stack" should be changed to "cloud".

        - CLI tool name
        - CLI tool commands
        - CLI tool documentation
        - REST API documentation
        - Any other references  

    2.2 - All references to the deployment enviroment "staging" should be changed to "stage".

        - Deployment environment names
        - Deployment environment references in documentation
        - Any other references

    2.3 - Change Pulumi Stack Naming convention:

        <deployment-id>-<environment>

    2.4 - Move current index.2.2.ts

        - Make index.ts the main Pulumi script
            - rename all references from index.2.2.ts to index.ts

        - Addendum Questions/Answers:
            - adjust package.json?
            - adjust tsconfig.json?

    2.5 - New Directory Structure and Directory Names.

        - Different Directory names,similar directory structure.

        2.5.1 - New root path for platform: 

            - /c/Users/Admin/Documents/Workspace/cloud

            - The new directory will be created later, during the implementation Task #3, below.

        2.5.2 - At new dir (./cloud/):

            - ./cloud/deploy/                       - replacement for the old ./aws/deploy/

            - ./cloud/tools/                        - replacement for the old ./admin/v2/
                - ./cloud/tools/api/
                - ./cloud/tools/cli/
                - ./cloud/tools/docs/
                - ./cloud/tools/templates/
                    - ./cloud/tools/templates/stacks/
                    - ./cloud/tools/templates/default/
                    - ./cloud/tools/templates/custom/
                    - ./cloud/tools/templates/docs/
                    - ./cloud/tools/templates/src/

            - ./cloud/stacks/                       - replacement for the old ./aws/build/
                - ./cloud/stacks/<stack-name>/docs
                - ./cloud/stacks/<stack-name>/src

                Examples:
                - ./cloud/stacks/network/docs
                - ./cloud/stacks/network/src

                - ./cloud/stacks/dns/docs
                - ./cloud/stacks/dns/src

        2.5.3 - Rename all stack subdirectories "resources" to "src":

            - From:     ./aws/build/<stack-name>/resources
            - To:       ./cloud/stacks/<stack-name>/src

        2.5.4 - Remove "v2" references from all paths.

            - From:     ./admin/v2/
            - To:       ./cloud/tools

            - From:     ./aws/build/<stack-name>/v2/resources
            - To:       ./cloud/stacks/<stack-name>/src        

    2.6 - Add improvements from the Pre-Implementation-Responses document

        Document: "./admin/v2/docs/Prompt-11 - Pre-Implementation - Responses.md"

        2.6.1 - Answer 1: Stack Dependencies.
        
            - Add recommendation described in the document's answer 1.2.1

            - Stack dependencies declared in stack templates.

        2.6.2 - Answer 2: Stack Template Creation.

            - Accept the suggestions:
                
                - Reuse the current templates for the 16 stacks.

                - User defines new stacks:
                    - Created via `multi-stack register-stack` command
                    - Automatically generates stack template file
                    - User provides: name, description, dependencies, configuration schema
                    - CLI creates the YAML template file

        2.6.3 - Answer 3: Partial Re-deployment.
        
            - Ensure smart, re-deploy is included as a core feature.

            - The orchestrator implements **smart dependency resolution**.

            - Ensure all enforcement rules described in the answer are included.

        2.6.4 - Answer 4: Multiple vs Single TypeScript Files.
        
            - Include this whole explanation as part of the new Architecture document (described in Task 4 - below).

        2.6.5 - Answer 5: Configuration Values.
        
            - Do NOT worry about this Answer, for now.

        2.6.6 - Answer 6: Layer-Based Execution Management

            - Include this whole explanation as part of the new Architecture document (described in Task 4 - below).

        2.6.7 - Answer 7: Progress Monitoring.

            - Include this whole explanation as part of the new Architecture document (described in Task 4 - below).

        2.6.8 - Answer 8: Cross-Stack References - Eliminating Hardcoding.

            - Include the proposed solution: "Combination of Solution 2 + Solution 4"

                - Use **Runtime Placeholders** for simple value passing
                - Use **DependencyResolver** when you need programmatic access to stack references

        2.6.9 - Answer 9: Other Hardcoded References.
        
            - Do NOT worry about this Answer, for now.

        2.6.10 - Answer 10: Multiple Similar Stacks.

            - Include this whole explanation as a dedicated new Addendum document (described in Task 4 - below), titled "Stack Cloning" .

        2.6.11 - Answer 11: Directory Creation Permissions.

            - Do NOT worry about this Answer, for now.

## Task 3 - Combine and Define New Architecture version

    - Combine ALL (100%) of the features (and feature details) described in the document Multi-Stack-Architecture-2.3, with ALL of the architectural changes described above in "#Task 2"; therefore defining a new architecture, which we will be refering to as Arch-v3 (Multi-Stack-Architecture-3.0).

## Task 4 - Create new set of Architecture documents with updated changes.

    - Platform naming guidelines:

        - "Multi-Stack-Architecture-3.0" is the name and version for the architecture.

        - Use "cloud-0.7" as the new name and version for the platform implementation.

        - "cloud" is the name for the platform, as well as the replacement name for the previous "multi-stack" tool.

        - "0.7" is the starting version for platform implementation (based on Multi-Stack-Architecture-3.0).

    - Generate a NEW Architecture Document:

        - Generate a NEW Architecture document, for version 3.0; based on Architecture 2.3.

        - Include ALL feartures and sections from the Architecture 2.3 document.

            - Make adjustments, as necessary, according to the Tasks #2, listed above.

            - Do not remove document sections (existing in 2.3). 

                - Move some sections to the Addendums, as instructed below.

        - Adjust and include ALL diagrams from Architecture 2.3  doc.

            - Make adjustments, as necessary, according to the Tasks #2, listed above.

        - Zero-code in the main Architecture document 
        
            - All code in Code Addendum document.

            - Simple pseudo-code allowed - sometimes to describe logic.

    - Additional Documents:
    
        - CLI full document
        - CLI testing document
        - CLI Quick Reference document

        - REST full document
        - REST Testing document
        - REST Quick Reference document

        - Deployment Manifesto document

    - Addendum Documents (separate documents):
        - Verification Architecture Addendum - Describing all of the details related to verification.
        - Stack Cloning Addendum - Full answer from Task 2.6.10 - Answer 10, go here.
        - Platform Code Addendum - All code used as exmpales or explanations, go here.
        - Progress Monitoring Addendum - Details and implementation, go here.
        - Stats Addendum - All statistics, go here.
        - Changes Addendum - All changes from Arch.2.,3 go here.
        - Answers Addendum - Answers to the questions below, go here.

    IMPORTANT: For each Additional document or Addendum document, make the necessary adjustments (structures, references, etc.), according to the Tasks #2, listed above.

## Task 5 - Implement

    5.1 - Implement Multi-Stack-Architecture-3.0 

        - Systematically implement all aspects of the Multi-Stack-Architecture-3.0; entirely.

        - Include in the implementation, all changes described in Tasks #2 (above); which by this point (in the Tasks execution list), should already be, part of Multi-Stack-Architecture-3.0. 

        - Re-use existing Pulumi stack code and documents, as detailed below in #5.4.

    5.2 - Ensure that implementation conforms with the described Multi-Stack-Architecture-3.0.

            - New Directory Structure and Directory Names.
            - Minimal Pulumi Specification.
            - Multi-Environment Architecture.
            - Configuration Architecture - Tiers, Flow.
            - Stack Registration Management.
            - Stack Creation - Flows and Features.
            - Stack Dependencies and Resolution.
            - Stack configuration files (Pulumi configuration files).
            - Stack source code files - including all of the necessary Pulumi .ts code.
            - Stack templates system - and template management tools and associated code.
            - Deployment flows and features.
            - Deplyment Manifest.
            - Deployment configuration files - including stack and environments stack deployment configuration.
            - Support Full Deployment Lifecycle.
            - Runtime Resolution Process.
            - Orchestration Engine.
            - State Management.
            - Error Handling.
            - CLI - All commands and params for the full feature set.
            - REST features, fully supporting all of CLI fearures and operations.
            - Security and Access Control
            - Verification and Validation tools for:
                - Configuration files.
                - Pulumi code.
                - CLI tool.
                - And any other verification tool, previously suggested in Arch.2.3.
            - Monitoring and Logging tools.
                - Create a new admin stack, if necessary - for the services necessary to support the goals set for Monitoring.
            - Known Issues.

    5.3 - Create new directory structure for the platform.

        - Create new directory structure as defined in Task #2.4 and Task #2.5, above.

    5.4 - Copy existing stacks (v2) and adjust.

        Copy existing stacks (directories and files) and adjust all copies and data (documents, code, file names, etc), to conform with Arch.v3.

        5.4.1 - Copy old stack documents.

            - COPY all of the existing files under each of the old stack/docs folders, to their new location; systematically adjusting names and contents of each file, as instructed on Task #2.

            - Ensure that the following documents are present in every stack/docs folder:

                - Stack_Prompt_Main.md - Main Prompt, used to define and generate the Stack_Definitions.md and Stack_Resources.md documents.
                - Stack_Prompt.Extra.md - Additional Prompt instructions, adding to the Main pPompt, if necessary.

                - Stack_Definitions.md - Stack definitions, as an outcome of the Main Prompt.
                - Stack_Resources.md - Stack resources, as an outcome of the Main Prompt.

                - Stack_History_Errors.md - Prompt execution errors, automatically created by the prompt execution process.
                - Stack_History_Fixes.md - Prompt execution fixes, automatically created by the prompt execution process.
                - Stack_History.md - Full Prompt execution history, automatically created by the prompt execution process.

            - All of the documents listed above (and for all stacks), should be copied to their new location; and their contents adjusted to Arch.v3, wherever necessary.

        5.4.2 - Copying old stack resources:
        
            - COPY all of the existing files under each of the old stack/v2/resources folders, to their new location (stack/src); systematically adjusting names and contents of each file, as instructed on Task #2.

            - Ensure that the following Pulumi files are present in every stack/src folder:

                - Pulumi.yaml
                - package.yaml
                - tsconfig.json
                - index.ts
            
            - All of the documents listed above (and for all stacks), should be copied to their new location; and their contents adjusted to Arch.v3, wherever necessary.

    5.5 - Consult existing platform documents and code, if necessary.

        - New Multi-Stack-Architecture-3.0 document defines the architecture implementation for the platform.

        - For *possible* platform code re-use, if necessary, consult previous documents:

            - Multi_Stack_Architecture.2.2.md
            - Prompt-9-1 - PULUMI_CONFIGURATION_QUESTIONS_ANSWERS.md
            - Prompt-9-3 - PULUMI_CONFIGURATION_FINAL_SOLUTION.md
            - Prompt-9-5 - DEPLOYMENT_INITIALIZATION_ANSWERS.md
            - Prompt-10 - Response - *.md (all "Prompt-10 - Responses" documents).

            IMPORTANT: Be aware that eariler documents might have information and code that might be outdated or even deprecated by Arch.v3.

    5.6 - Implement all CLI commands.

        - Implement the full list of features (as described in Arch.v3) for the CLI

        - Create tools and unit tests to verify and test the CLI functionality.

    5.7 - Implement all validation and verification commands and test them (via unitests or any other tests).

        - If not possible to run the verifications, then include in the Verification Architecture Addendum, instructions on how to perform all validations and verificaitons, using the CLI tool or any other means.

    5.8 - Generate a set of "generic" Documents Templates.

        - Generic, but adjusted to Arch.v3.

        - Based on all of the docs listed on Task 5.4.1, above.

        - To be used as Prompt templates for new stacks.

        - To be placed under "./cloud/tools/templates/docs/"

    5.9 - Generate a set of "generic" Pulumi files Templates.

        - Generic, but adjusted to Arch.v3.

        - Based on all of the docs listed on Task 5.4.2, above.

        - To be used as templates for new stacks.

        - To be placed under "./cloud/tools/templates/src/"

    5.10 - No need to backup or migrate any deployments.

    5.11 - REST API should be implemented as much as possible.

        - Implement the full list of features (as described in Arch.v3) for the REST API.   
        - Implement as much as possible - we will refine the implementaion later.
        - Create a new, separate REST document, describing the missing implementaion details and making suggestions for all of the missing parts.

    5.12 - Database layer for platform metadata.

        - At this time, we will not implement database integration with the platform.

        - Create a new, separate document, describing *where* the platform is critically needing a database, and provide suggestions for integrating a database with Arch.v3.

    5.13 - Monitoring WebSockets should be implemented as much as possible.

        - Implement the full list of features (as described in Arch.v3) for Monitoring (including the necessary services for WebSockets).
        - Do not make any AWS deployments for this, at this time - only implement (write code and possible documents, guiding the aws deployment of the services that need to exist).   
        - Implement as much as possible - we will refine the implementaion and deplyment later.
        - Create a new, separate  document, describing all of the missing implementaion details and making suggestions for all of the missing parts.

    5.14 - Generate a new document, detailing how to compile and get all of the code ready for execution.

        - Pulumi stacks
        - CLI tool
        - REST API
        - Monitoring tool
        
