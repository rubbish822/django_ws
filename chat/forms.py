#!usr/bin/env python 
# -*- coding:utf-8 _*-
"""
@author:-
@file: forms.py 
@version:
@time: 2019/06/26 

"""
from django import forms

from . import models


class RoomForm(forms.Form):
    name = forms.CharField(
        max_length=64, required=True
    )
    content = forms.CharField(
        max_length=128, required=False
    )
