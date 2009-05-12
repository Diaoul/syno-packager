if [ "$1" != "" ]; then
	SPK_NAME=$1
fi
if [ "$2" != "" ]; then
	SPK_VERSION=$2
fi
if [ "$3" != "" ]; then
	SPK_DESC=$3
fi
if [ "$4" != "" ]; then
	SPK_MAINT=$4
fi
if [ "$5" != "" ]; then
	SPK_ARCH=$5
fi
if [ "$6" != "" ]; then
	SPK_RELOADUI=$6
fi

if [ "$SPK_NAME" = "" ]; then
	echo Need at least a package name.
	exit 1
fi

if [ "$SPK_VERSION" = "" ]; then
	SPK_VERSION=unknown
fi
if [ "$SPK_DESC" = "" ]; then
	SPK_DESC="No description"
fi
if [ "$SPK_MAINT" = "" ]; then
	SPK_MAINT=Unknown
fi
if [ "$SPK_ARCH" = "" ]; then
	SPK_ARCH=noarch
fi
if [ "$SPK_RELOADUI" = "" ]; then
	SPK_RELOADUI=yes
fi

if [ ! -d out ]; then
	echo Are you running this from a dir other than the repo root?
	exit 1
fi

SPK_DIR=out/spk
INFO_FILE=$SPK_DIR/INFO

mkdir -p $SPK_DIR

echo package=\"$SPK_NAME\" > $INFO_FILE
echo version=\"$SPK_VERSION\" >> $INFO_FILE
echo description=\"$SPK_DESC\" >> $INFO_FILE
echo maintainer=\"$SPK_MAINT\" >> $INFO_FILE
echo arch=\"$SPK_ARCH\" >> $INFO_FILE
echo reloadui=\"$SPK_RELOADUI\" >> $INFO_FILE

mkdir -p $SPK_DIR/scripts
cp scripts/spk/* $SPK_DIR/scripts

cd out/root && tar czf ../../$SPK_DIR/package.tgz *
cd ../../$SPK_DIR
tar cf ../$SPK_NAME-$SPK_VERSION.spk *

