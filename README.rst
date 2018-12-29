Given ATCO codes, shows the next bus times at given stops.

This is particularly useful bound to a keybinding and passed to
libnotify’s ``notify-send`` program, so you can quickly get an overview
of the next buses at stops you care about.

You must set ``WTB_APP_ID`` and ``WTB_APP_KEY`` to an app ID and app key
valid at `TransportAPI`_.

Usage
=====

Pass ATCO codes with ``-a``. See below for how to find them.

::

   % WTB_APP_ID=xxx WTB_APP_KEY=xxx wtb -a 490004733D -a 4100008HAYRS
   Canada Water Bus Station (Stop D) (490004733D):
   - 199 to Canada Water: Due, 11 min, 25 min
   - C10 to Canada Water: 3 min, 9 min, 19 min
   - 1 to Canada Water: 8 min, 20 min
   - P12 to Surrey Quays: 11 min, 20 min
   - 225 to Canada Water: 13 min
   - LO-M to Canada Water: 23 min

   Haymarket Bus Station (R) (4100008HAYRS):
   - 44 to Dinnington: 4 min, 34 min, 1 hr 4 min
   - 43 to Cramlington Manor Walks Dudley Lane: 11 min, 41 min
   - 45 to Dinnington: 19 min, 49 min, 1 hr 19 min
   - 43 to Morpeth Bus Station: 26 min

How do I find ATCO codes?
=========================

-  For London bus stops, it’s in the URI. For example, in `this URI`_,
   “490004733D” is the ATCO code.
-  For non-London, try the following:

   1. Navigate to the bus stop on OpenStreetMap
   2. On the right, click “layers”
   3. Tick “map data”
   4. Click on the bus stop on the map
   5. On the left, you should see the ATCO code (possibly as something
      like ``naptan:AtcoCode``)

.. _TransportAPI: https://www.transportapi.com/
.. _this URI: https://tfl.gov.uk/bus/stop/490004733D/canada-water-bus-station

Installation
============

To install the latest stable version from PyPi:

.. code::

    $ pip install -U whensthebus

To install the latest development version directly from GitHub:

.. code::

    $ pip install -U git+https://github.com/cdown/whensthebus.git@develop
