#coding: utf-8
'''
Created on 2014-3-31

@author: Administrator
'''
import pygame
from PIL import Image
from StringIO import StringIO
#from utils.color_convert import HTMLColorToRGB
from utils.color_convert import HexColorToRGB



def start_x(width, line_width, align="left"):
    if align=="left":
        return 0
    elif align=="center":
        return (width-line_width)/2
    elif align=="right":
        return width-line_width
    

def txt2img(font, font_file):
    content = font.content
    font_size = int(font.size)
    #font_color = HTMLColorToRGB(font.color)
    font_color = HexColorToRGB(int(font.color))
    #print font_color
    font_align = font.align
    if font_align not in ("left", "center", "right"):
        font_align = "left"
    pygame.font.init()
    #print font_file, font_file.encode('gbk')
    #print dir(font), "hello", font.get("bold", None)
    import sys
    # pygame_font = pygame.font.Font(font_file.encode(sys.getdefaultencoding()), font_size)
    try:
        pygame_font = pygame.font.Font(font_file.encode("utf-8"), font_size)
    except:
        pygame_font = pygame.font.Font(font_file.encode("gbk"), font_size)
    if font.has_key("bold") and font.bold == 1:
        pygame_font.set_bold(True)
    #pygame_font.set_italic(True)
    #pygame_font.set_underline(True)
    
    paragraph_list = content.split('\r')
    #print font_size, content.replace('\r', ''), paragraph_list
    line_space, vertical_pos, line_width = 5, 0, 0
    
    try:
        width = int(font.width)
        height = int(font.height)
    except: width, line_height = 0, 0
 
    if width==0 or height==0:
        width, line_height, line_count = 0, 0, 0
        width_dict = {}
        index = 1
        for paragraph in paragraph_list:
            line_count += 1
            font_size = pygame_font.size(paragraph)
            if font_size[0] > width: width = font_size[0]
            if font_size[1] > line_height: line_height = font_size[1]
            width_dict[index] = font_size[0]
            index += 1
        
        height = line_height * line_count + line_space*(line_count - 1)
        #print "width, height", width, height, line_height, line_count, font_file
        img = Image.new('RGBA', (width, height))
        index = 1
        for paragraph in paragraph_list:
            if len(paragraph) == 0:
                vertical_pos += line_height + line_space
                continue
            rtext = pygame_font.render(paragraph, True, font_color)
            buffer_img = StringIO()
            pygame.image.save(rtext, buffer_img)
            buffer_img.seek(0)
            
            line = Image.open(buffer_img)
            img.paste(line, (start_x(width, width_dict[index], font_align), vertical_pos))
            vertical_pos += line_height + line_space
            index += 1
        pygame.font.quit()
        return img
    else:
        img = Image.new('RGBA', (width, height))
        for paragraph in paragraph_list:
            line_height = pygame_font.size(paragraph)[1]
            if len(paragraph) == 0:
                vertical_pos += line_height + line_space
                continue
            line_character = ""
            for character in paragraph:
                c_width = pygame_font.size(character)[0]
                line_width += c_width
                
                if line_width > width:
                    #print character, line_character, c_width, vertical_pos, line_width
                    buffer_img = StringIO()
                    rtext = pygame_font.render(line_character, True, font_color)
                    pygame.image.save(rtext, buffer_img)
                    buffer_img.seek(0)
                    
                    line = Image.open(buffer_img)
                    img.paste(line, (0, vertical_pos))
                    vertical_pos += line_height + line_space
                    if vertical_pos >= height:
                        pygame.font.quit()
                        return img
                    
                    line_character = character
                    line_width = c_width
                else:
                    line_character += character
            if line_width > 0:
                #print "single line", line_character, line_width
                buffer_img = StringIO()
                rtext = pygame_font.render(line_character, True, font_color)
                pygame.image.save(rtext, buffer_img)
                buffer_img.seek(0)
                
                line = Image.open(buffer_img)
                img.paste(line, (start_x(width, line_width, font_align), vertical_pos))
                vertical_pos += line_height + line_space
                if vertical_pos >= height:
                    pygame.font.quit()
                    return img
                
                line_character = ""
                line_width = 0
        pygame.font.quit()
        #print img.size
        return img
    








    