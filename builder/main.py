# Copyright 2017-present Federico Luis Pinna Gonzalez <fedepinna13@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os.path import join
from time import sleep
import subprocess
from sys import stderr

from SCons.Script import (ARGUMENTS, COMMAND_LINE_TARGETS, AlwaysBuild,
                          Builder, Default, DefaultEnvironment)

from platformio.util import get_serialports


def HIDUpload(target, source, env): # Uploader for DuinoBotv1x_HID, DuinoBotv2x_HID

    platform = env.PioPlatform()

    firmware_path = join(env.subst("$BUILD_DIR"), "firmware.hex")
    tool_flags = env.subst("$UPLOADERFLAGS")

    tool_path = platform.get_package_dir("tool-duinobothid") or ""
    tool_path += "\\" + env.subst("$UPLOADER")+".exe"

    shell_command = tool_path + " " + tool_flags + " " + firmware_path
    proc = subprocess.Popen(shell_command, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = proc.communicate()

    if "Done." not in err:
        stderr.write('\033[1m'+'\033[91m' + "UPLOAD FAILED: ")
        stderr.write(err)
    else:
        print  '\033[1m'+'\033[92m'+"UPLOAD COMPLETED!"

def BeforeUpload(target, source, env):  # pylint: disable=W0613,W0621

    if "program" in COMMAND_LINE_TARGETS:
        return

    upload_options = {}
    if "BOARD" in env:
        upload_options = env.BoardConfig().get("upload", {})

    # Deprecated: compatibility with old projects. Use `program` instead
    if "usb" in env.subst("$UPLOAD_PROTOCOL"):
        upload_options['require_upload_port'] = False
        env.Replace(UPLOAD_SPEED=None)

    if env.subst("$UPLOAD_SPEED"):
        env.Append(UPLOADERFLAGS=["-b", "$UPLOAD_SPEED"])

    # extra upload flags
    if "extra_flags" in upload_options:
        env.Append(UPLOADERFLAGS=upload_options.get("extra_flags"))

    if upload_options and not upload_options.get("require_upload_port", False):
        return

    env.AutodetectUploadPort()
    env.Append(UPLOADERFLAGS=["-P", '"$UPLOAD_PORT"'])

    if env.subst("$BOARD") in ("raspduino", "emonpi"):

        def _rpi_sysgpio(path, value):
            with open(path, "w") as f:
                f.write(str(value))

        pin_num = 18 if env.subst("$BOARD") == "raspduino" else 4
        _rpi_sysgpio("/sys/class/gpio/export", pin_num)
        _rpi_sysgpio("/sys/class/gpio/gpio%d/direction" % pin_num, "out")
        _rpi_sysgpio("/sys/class/gpio/gpio%d/value" % pin_num, 1)
        sleep(0.1)
        _rpi_sysgpio("/sys/class/gpio/gpio%d/value" % pin_num, 0)
        _rpi_sysgpio("/sys/class/gpio/unexport", pin_num)
    else:
        if not upload_options.get("disable_flushing", False):
            env.FlushSerialBuffer("$UPLOAD_PORT")

        before_ports = get_serialports()

        if upload_options.get("use_1200bps_touch", False):
            env.TouchSerialPort("$UPLOAD_PORT", 1200)

        if upload_options.get("wait_for_upload_port", False):
            env.Replace(UPLOAD_PORT=env.WaitForNewSerialPort(before_ports))


env = DefaultEnvironment()

env.Replace(
    AR="avr-ar",
    AS="avr-as",
    CC="avr-gcc",
    CXX="avr-g++",
    OBJCOPY="avr-objcopy",
	RANLIB="avr-ranlib",
    SIZETOOL="avr-size",

    ARFLAGS=["rcs"],

    ASFLAGS=["-x", "assembler-with-cpp"],

    CFLAGS=[
        #"-std=gnu11",
		#"-fno-fat-lto-objects"
    ],

    CCFLAGS=[
        "-g",  # include debugging info (so errors include line numbers)
        "-Os",  # optimize for size
        "-w",  # show warnings
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
        #"-flto",
        "-mmcu=$BOARD_MCU"
    ],

    CXXFLAGS=[
        "-fno-exceptions",
        #"-fno-threadsafe-statics",
        #"-fpermissive",
        #"-std=gnu++11"
    ],

    CPPDEFINES=[("F_CPU", "$BOARD_F_CPU")],

    LINKFLAGS=[
        "-Os",
        "-mmcu=$BOARD_MCU",
        "-Wl,--gc-sections",
        #"-flto",
        "-fuse-linker-plugin"
    ],

    LIBS=["m"],

    SIZEPRINTCMD='$SIZETOOL --mcu=$BOARD_MCU -C -d $SOURCES',

    PROGNAME="firmware",
    PROGSUFFIX=".elf"
)

env.Append(
    ASFLAGS=env.get("CCFLAGS", [])[:],

    BUILDERS=dict(
        ElfToEep=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "ihex",
                "-j",
                ".eeprom",
                '--set-section-flags=.eeprom="alloc,load"',
                "--no-change-warnings",
                "--change-section-lma",
                ".eeprom=0",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".eep"
        ),

        ElfToHex=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "ihex",
                "-R",
                ".eeprom",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".hex"
        )
    )
)

#Uploads

if env.subst("$UPLOAD_PROTOCOL") in ("avr109", "duinobothid"):

	env.Replace(
		UPLOADER="hid_bootloader_cli",
		UPLOADERFLAGS=[
			"-mmcu=$BOARD_MCU",
			"-r",  # wait for device to apear
            "-v"  # verbose output
		],
		UPLOADHEXCMD='$UPLOADER $UPLOADERFLAGS $SOURCES'
	)

if env.subst("$UPLOAD_PROTOCOL") in ("arduino", "duinobothid"):

    env.Replace(
		UPLOADER="hiduploader",
		UPLOADERFLAGS=[
			"-mmcu=$BOARD_MCU",
            "-v",
            "-usb=" + env.BoardConfig().get("upload.usb_vid") + ":"
             + env.BoardConfig().get("upload.usb_pid")
		],
		UPLOADHEXCMD='$UPLOADER $UPLOADERFLAGS $SOURCES'
	)

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_firm = join("$BUILD_DIR", "firmware.hex")
else:
    target_elf = env.BuildProgram()
    target_firm = env.ElfToHex(join("$BUILD_DIR", "firmware"), target_elf)

AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm, target_firm)

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)

#
# Target: Upload by default firmware file
#

target_upload = env.Alias(
    "upload",target_firm,env.VerboseAction(HIDUpload,"Upload firmware..."))
AlwaysBuild(target_upload)

#
# Setup default targets
#

Default([target_buildprog, target_size])
