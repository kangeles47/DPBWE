# Bayesian Data Integration Framework for the Development of Component-level Fragilities Derived from Multiple Post-Disaster Datasets

## Project Overview
### Context
- The design of targeted mitigation strategies and policies to reduce disaster-related losses across entire regions requires the realization of building-specific, component-level regional loss assessments. However, such highly granular loss assessments face a unique challenge in sourcing reliable fragilities to conduct damage assessment of actual constructed buildings; this is particularly an issue for the case of wind-vulnerable structures. 

### Data Opportunity
- Field observations from reconnaissance missions 
  - [Growing efforts](https://www.steer.network/) to ensure these surveys capture component-level damage in an unbiased fashion
  - Increasing accessibility to this data through [online repositories](https://www.designsafe-ci.org/recon-portal/)
- New forms of post-disaster datasets emerging as a result of remote sensing technologies, street-level panoramic imaging, and the ever-growing open data landscape

### Project Goal

*Formalize a replicable, automated workflow for the development of component-level fragilites that utilizes multiple post-disaster datasets* that:
1. Generalizes the process of sample building selection beyond the requirements of a specific building archetype and hazard
2. Formalizes the integration of damage data without relying on the presence of specific post-disaster datasets
3. Supports fragility model development for a range of data availability use cases

### The How

Schematic overview of Bayesian Data Integration framework:

![My Image](Framework.png)

Fragilities are automatically created for a given building's components according to a specified damage scale (associated with a specific hazard) through a set of subroutines that automate:
- Building sample selection
  - Here we define a set of similitude criteria which evaluate feature and load path similarity between potential samples in an inventory and a given reference building
- Damage data querying and integration
  - We formalized a data utility index that evaluates each available damage observation across the following data quality measures: granularity, precision, accuracy, perishability -- this allows the framework to automatically identify the most reliable and granular observation for each sample building
- Fragility model updating
  - This implementation utilizes the [PyMC3](https://docs.pymc.io/en/v3/index.html) library and available simulation-based fragilities

### Broader Impacts
- Generated observation-informed fragilities can now be used to support regional damage assessments of actual constructed buildings (less dependence on simulation-based fragilities populated using generic building models)
  - Component-level fragilities can be calibrated for specific regions (e.g., Florida's Bay County)
  - Component-level fragilities can be calibrated to account for changes in construction practices (e.g., homes built before and after the instantiation of the Florida Building Code)
- Data-driven Bayesian approach reveals hazard intensities, building classes, and damage measures to be targeted in future, federally-funded reconnaissance missions

## Publications
Note: the research developments described above have been formalized into a manuscript that is currently under review in [Structural Safety](https://www.journals.elsevier.com/structural-safety) and the link for this article will be included once it is available.

In the manuscript, the framework is applied to deliver roof cover fragilities for the following two case studies: 
1. Hurricane Michael - single family homes with asphalt shingle roofs (considering construction before/after Florida Building Code) using [field observations](https://www.designsafe-ci.org/data/browser/public/designsafe.storage.published/PRJ-2113) and post-disaster building [permit data](https://applications.baycountyfl.gov/Search/permit.aspx) from Florida's Bay County
2. Hurricane Irma - instutional buildings with built-up roofs using [field observations](https://www.designsafe-ci.org/data/browser/public/designsafe.storage.published//PRJ-1828) and [regional damage data from FEMA](https://www.fema.gov/about/openfema/data-sets#hazard)

## Overview of Skills Necessary to Develop this Project
### Data Science
**Data Mining** 
- Web-scraping ([scrapy](https://scrapy.org/) Python package) to extract parcel tax assessor data from the Bay County Property Appraiser's website
- Application Programming Interface ([OpenFEMA API](https://www.fema.gov/about/openfema/api)) to extract damage observations for a case study in Hurricane Irma

**Data Wrangling** 
- Feature clean-up: establishing data fields, filling in missing values, removing duplicates

**Data Exploration**
- [Pandas](https://pandas.pydata.org/) to obtain an overview of building archetypes in Florida's Bay County
- [Matplotlib](https://matplotlib.org/) to plot distributions of damage observations in Hurricane Irma exposure region and to visualize distributions of the hazard intensity across exposure regions

**Feature Engineering**
- Integrated parcel tax assessor data along with other open data to populate additional features in building models necessary to automate sample selection process. Additional open data sources include:
  - Data from the Department of Energy's Residential and Commercial Reference Buildings
  - Modern codes and standards
  - Building footprint data 

### Probability/Statistics
Bayesian model updating, Gaussian mixture model (Expectation-Maximization), Cumulative distribution functions, Maximum likelihood estimation

### Civil/Structural Engineering
Knowledge of fragility curves, damage and loss assessments, building load paths, modern building codes, Floridian construction practices, wind profiles, and roof pressure distributions. Understanding of the current state-of-practice in hurricane regional loss assessment and new efforts in open-source loss modeling. 
