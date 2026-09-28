# CamView

A camera-control and live-view application for scientific imaging systems, developed for experimental physics applications.

CamView provides a graphical interface for controlling and monitoring multiple scientific cameras used in experimental setups. The application was originally developed in Python and later migrated to a C++/Qt implementation to provide a more robust and maintainable desktop application.

## Features

- Live camera preview
- Support for multiple scientific camera systems
- Camera initialization and configuration
- Camera selection and management
- Automated image acquisition
- Network-based communication between components
- Configurable acquisition settings
- Integration with camera vendor SDKs
- Graphical user interface for experimental use
- Modular architecture for adding additional camera systems

## Supported Cameras

The project was developed with several scientific camera systems, including:

- **PCO Pixelfly**
- **Andor iXon EMCCD**
- **FLIR Grasshopper**

Camera communication is implemented through the respective manufacturer SDKs and interfaces.

## Architecture

````text
                    ┌─────────────────────┐
                    │       CamView       │
                    │    Qt GUI / C++     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌───────────┐    ┌───────────┐    ┌───────────┐
        │    PCO    │    │   Andor   │    │   FLIR    │
        │  Pixelfly │    │   iXon    │    │Grasshopper│
        └───────────┘    └───────────┘    └───────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                      Image Acquisition
                         & Processing
