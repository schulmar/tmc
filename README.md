Current State
=============

The package as is worked on a server I hosted a while ago.
It is reasonable stable to run unsupervised but I cannot guarantee that it will not hang.

I have no time at hand to progress further, 
but maybe someone with the same intentions might want to go on from here.

Be warned that the code might be as messy as the folder structure.

History
=======

I started this project some time ago because I was fed up with the drawbacks of existing controllers for TrackMania.
I will give some examples what annoyed me most on XAseco:

 - written in PHP there is no multi-threading
 - grown over a large amount of time it has many relics that hinder the design and make programming a pain
 - including new modules could create problems because of dependencies and name clashes (everything in global scope)

Because of these limitations and because I had some spare time I started working on this project.
As I wanted to use multi-threading PHP was not the language of choice but rather Python.

Design
======

The main principles for the design I chose

simple usage
: easy interaction for the users on the server and for the programmers

fast reaction
: each response should not take longer than one second (without network latency)

low cpu time consumption
: if there is nothing to do then do nothing!

As true parallel multi threading is not possible with every python implementation (because of the GIL) 
I chose a design where each plugin would run in its own process 
(which could even enable restarting failed plugins without restarting the whole controller).

The central component is the PluginManager, 
that communicates with each plugin via two pipes and redirects their requests to other plugins.