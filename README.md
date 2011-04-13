Syno-Packager
=============

All-in-one tool to cross-compile and make Synology Packages (SPK)


HOW-TO
------
1. Grab your copy of syno-packager `git clone git://github.com/Diaoul/syno-packager.git` or fork it if you want to contribute
2. Download precompiled toolchains (see [here](https://github.com/Diaoul/syno-packager/tree/master/ext/precompiled/))
3. Download external packages (see [here](https://github.com/Diaoul/syno-packager/tree/master/ext/packages/))
4. Create the rules you need in rules.mk in the corresponding category folowing multiple examples you can find in it
5. Create a myPackage.mk with variable definitions folowing otherPackages.mk examples
6. Do some debug using basic rules (see below)
7. Once everything is compiling well, make the folder src/myPackage using folowing src/otherPackages examples
8. Test the SPK by yourself
9. Release it !
10. Please submit a Pull Request to make Syno-Packager even better


Basic rules
-----------
* Want to try to build your package ? `make -f myPackage.mk`
* This is a real mess, how do I clean it ? `make -f myPackage.mk clean`
* Just want to try to compile mySubPackage which is a dependency of myPackage (ie OpenSSL) ? `make -f myPackage.mk mySubPackage`
* Now everything is compiled, how do I make the SPK for my arch ? `make -f myPackage.mk spk`
* How do I test it from nothing ? `make -f myPackage.mk release`
* Oh my god this is working, how do I share it ? `make -f myPackage.mk realeaseall` then put that online


Help
----
Get some help typing `make help` and


Downloads
---------
Official SPKs can be dowloaded directly from [Synology's website](http://www.synology.com/support/download.php)


Documentation
-------------
[A wiki about SPKs](http://forum.synology.com/wiki/index.php/Synology_package_files) is available but a little outdated as some things have changed since DSM 3
[3rd-Party Apps Integration Guide](http://www.google.com/url?sa=t&source=web&cd=1&ved=0CBYQFjAA&url=http%3A%2F%2Fdownload.synology.com%2Fdownload%2Fds%2Fuserguide%2FSynology%2520NAS%2520Server%25203rd-Party%2520Apps%2520Integration%2520Guide.pdf&rct=j&q=synology%20pdf&ei=tYOlTfbaH4uEhQeZ4fXNCQ&usg=AFQjCNF1gASkfe_ze9oKlR3C-F58mnsuEA&sig2=USi8aVko-VKrA_F9UcB6zA&cad=rja) is very handy and up-to-date


