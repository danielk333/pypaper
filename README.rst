pypaper
=========

Feature list
-------------

* Harmonization of bibtex identifiers
* Searching bibtex database based on logic combinations of regular expression searches of bibtex field values
* Pickup of multiple bibtex files and combining into a single database
* Tracking of PDF's that are linked to bibtex entries for simplifying research
* Easy to use terminal control
* Direct interface with NASA ADS for fetching bibtex entries
* Possibility to automatically download paper PDFs when available from NASA ADS system
* Convenience functions for attempting to fill database with PDF version of papers
* No specific database required, function directly on bibtex files and PDFs in a folder structure

To run
---------------

.. code-block:: bash

   pypaper


To install
-----------------

.. code-block:: bash

   pip install git+https://github.com/danielk333/pypaper

or 

.. code-block:: bash

   git clone https://github.com/danielk333/pypaper
   cd pypaper
   pip install .


Example
---------------

.. code-block:: bash

    $ pypaper
    Bib load: 357 entries loaded
    DOCS load: 73 papers found
    Starting prompt...

    > bib author=Kastinen & year=2018
    0   [pdf]: Kastinen2018Determining_all_ambiguities_in_direction_of_arrival_measured_by_radar_systems
    1   [pdf]: Kastinen2018Orbital_uncertainties_in_radar_meteor_head_echoes
    > bibview 1
    Kastinen2018Orbital_uncertainties_in_radar_meteor_head_echoes
    - year: 2018
    - title: {Orbital uncertainties in radar meteor head echoes}
    - pages: 92-98
    - month: January
    - booktitle: Proceedings of the International Meteor Conference
    - author: {Kastinen}, Daniel and {Kero}, Johan
    - adsurl: https://ui.adsabs.harvard.edu/abs/2018pimo.conf...92K
    - adsnote: Provided by the SAO/NASA Astrophysics Data System
    - ENTRYTYPE: inproceedings
    - ID: Kastinen2018Orbital_uncertainties_in_radar_meteor_head_echoes
    > 
    > ads q='author: "Chambers" title:"Symplectic Integrator ", year:1990-2000'
    [?] Add to bibtex and attempt PDF fetch?: 
       X Chambers, J. E. [1999]: ['A hybrid symplectic integrator that permits close encounters between massive bodies']
       o Chambers, J. E. et. al [2000]: ['Pseudo-High-Order Symplectic Integrators']
       X Chambers, J. E. [1999]: ['A symplectic integration scheme that allows close encounters between massive bodies.']
     > o Murison, M. A. et. al [1999]: ['On Computer Algebra Generation of Symplectic Integrator Methods']

    Skipped 1 duplicates
    Added 1 entries
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   323  100   323    0     0    372      0 --:--:-- --:--:-- --:--:--   372
    100  160k    0  160k    0     0  64575      0 --:--:--  0:00:02 --:--:--  254k
    PDF found and saved to database
    
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   323  100   323    0     0    375      0 --:--:-- --:--:-- --:--:--   375
    100  114k    0  114k    0     0  59593      0 --:--:--  0:00:01 --:--:--  195k
    PDF found and saved to database
    
    Bib load: 358 entries loaded
    DOCS load: 75 papers found
    > 
