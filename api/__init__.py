#coding: utf-8
import pygame
from PIL import Image, ImageFont, ImageDraw
from StringIO import StringIO


def start_x(width, line_width, align="left"):
    if align=="left":
        return 0
    elif align=="center":
        return (width-line_width)/2
    elif align=="right":
        return width-line_width
    
def txt2img_pil(font_file, content, font_size, font_color, width, height, align="right"):
    #print "txt2img", font_file, content, font_size, font_color, width, height
    #pygame.font.init()
    #import sys
    #print sys.getdefaultencoding()
    #pygame_font.set_bold(True)
    #pygame_font.set_italic(True)
    #pygame_font.set_underline(True)
    #font = ImageFont.truetype(font_file.encode(sys.getdefaultencoding()), font_size)
    font = ImageFont.truetype(font_file, font_size)
    
    paragraph_list = content.split('\r')
    #print font_size, content.replace('\r', ''), paragraph_list
    line_space, vertical_pos, line_width = 5, 0, 0
    
    img = Image.new('RGBA', (1024, 800))
    dr = ImageDraw.Draw(img)
    #print "img = Image.new('RGBA', (width, height))"
    for paragraph in paragraph_list:
        dr.text((0, vertical_pos), paragraph, font=font, fill="#ff00ff")
    return img
    

def txt2img(font_file, content, font_size, font_color, width, height, align="left"):
    #print "txt2img", font_file, content, font_size, font_color, width, height
    pygame.font.init()
    import sys
    # print sys.getdefaultencoding()
    # print 'font_file=', font_file
    try:
        pygame_font = pygame.font.Font(font_file.encode(sys.getdefaultencoding()), font_size)
    except Exception as e:
        pygame_font = pygame.font.Font(font_file, font_size)
    #print "pygame.font.Font"
    #pygame_font.set_bold(True)
    #pygame_font.set_italic(True)
    #pygame_font.set_underline(True)
    
    paragraph_list = content.split('\n')
    #print font_size, content.replace('\r', ''), paragraph_list
    line_space, vertical_pos, line_width = 5, 0, 0
    
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
                index += 1
                continue
            rtext = pygame_font.render(paragraph, True, font_color)
            buffer_img = StringIO()
            pygame.image.save(rtext, buffer_img)
            buffer_img.seek(0)
            
            line = Image.open(buffer_img)
            img.paste(line, (start_x(width, width_dict[index], align), vertical_pos))
            vertical_pos += line_height + line_space
            index += 1
        pygame.font.quit()
        return img
    else:
        #print "img = Image.new", width, height
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
                img.paste(line, (start_x(width, line_width, align), vertical_pos))
                vertical_pos += line_height + line_space
                if vertical_pos >= height:
                    pygame.font.quit()
                    return img
                
                line_character = ""
                line_width = 0
        pygame.font.quit()
        #print img.size
        return img
    

