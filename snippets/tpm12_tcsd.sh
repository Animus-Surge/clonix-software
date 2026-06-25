#!/bin/bash

groupadd tss
useradd -M -g tss tss

tcsd -f &
