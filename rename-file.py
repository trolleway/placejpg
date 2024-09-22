#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, subprocess, logging, argparse, sys, pprint, datetime
import pywikibot

import trolleway_commons
from model_wiki import Model_wiki
from fileprocessor import Fileprocessor
from urllib.parse import urlparse
import csv
from tqdm import tqdm


parser = argparse.ArgumentParser(
    description=" ")

parser.add_argument('--pagename', type=str, required=False, help='Wikipedia filepage')
parser.add_argument('--csv', type=str, required=False, help='list of page names for batch rename')
parser.add_argument('--wikidata', type=str, required=True)
parser.add_argument('--suffix', type=str, required=False,default='')
parser.add_argument('--prefix', type=str, required=False,default='')
parser.add_argument('--rationale', type=int, required=False,default=2,help='1.	At the original uploader’s request, 2 .	To change from a meaningless or ambiguous name to a name that describes what the image particularly displays 3 obvious errors 4  harmonize the names of a set of images 5 violation of Commons’ policies and guidelines 6 Non-controversial maintenance and bug fixes')
parser.add_argument("--verify", action="store_const",
                    required=False, default=False, const=True)

class Helper_rename:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)
    
    cachedir='maintainer_cache'
    fileprocessor = Fileprocessor()

    def dowload_or_cache_read(self,FilePage)->str:
        if not os.path.isdir(self.cachedir):
            os.makedirs(self.cachedir)
            
        url = FilePage.get_file_url()   
        pageid = FilePage.pageid
        ext = os.path.splitext(os.path.basename(urlparse(url).path))[1]
        fn=os.path.splitext(os.path.basename(urlparse(url).path))[0]
        filepath = os.path.join(self.cachedir, os.path.basename(urlparse(url).path) )
        filepath = os.path.join(self.cachedir,fn+ext )
        if os.path.isfile(filepath):
            return filepath
        FilePage.download(filename=filepath)
        return filepath
     
    
    def get_dt_from_FilePage(self,filepage)->datetime.datetime:
        local_filepath=self.dowload_or_cache_read(filepage)
        modelwiki = Model_wiki()
        dt_obj=self.fileprocessor.image2datetime(local_filepath)
        return dt_obj
    
    def generate_filename(self,pagename,wikidata)->str:
        
        assert pagename
        # Login to your account
        site = pywikibot.Site('commons', 'commons')
        site.login()
        site.get_tokens("csrf")  # preload csrf token

        file_page = pywikibot.FilePage(site, pagename)

        dt_obj = helper_renamer.get_dt_from_FilePage(file_page)

        objectnames=modelwiki.get_wikidata_simplified(wikidata)['labels']
        filename=file_page.get_file_url()
        commons_filename = self.fileprocessor.commons_filename(
                filename, objectnames, wikidata, dt_obj,add_administrative_name=False)
        return commons_filename
    
    def generate_rename_template(self,new_name:str,rationale:int)->str:
        assert rationale >= 0 
        assert rationale <=6
        text='{{Rename|1='+new_name+'|2='+str(rationale)+'|3=human-readable name from wikidata name}}'
        return text
    
    def prepend_text(self,text,new_text,check='')->str:
        if check in text:
            print(check+' already in text')
            return None
        text = new_text + "\n"+text
        return text
    
    def append_suffix(self,fns,suffix):
        if suffix=='':
            return fns
        assert fns.count('.')==1
        fns=fns.replace('.','_'+suffix+'.')
        return fns
    
    def append_prefix(self,fns,prefix):
        if prefix=='':
            return fns
        assert fns.count('.')==1, 'invalid text: '+fns
        fns = f'{prefix}_{fns}'

        return fns    

    
    def prepend_text_page(self,pagename,rename_template_text):
        assert pagename
        # Login to your account
        site = pywikibot.Site('commons', 'commons')
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        file_page = pywikibot.FilePage(site, pagename)

        new_page_text = helper_renamer.prepend_text(file_page.text,rename_template_text,'{{Rename')
        if new_page_text is None:
            return None
        page_not_need_change = True
        if new_page_text!=file_page.text:page_not_need_change = False

        file_page.text = new_page_text
        if page_not_need_change == False:
            file_page.save('propose rename')

        return True        


if __name__ == '__main__':
    
    args = parser.parse_args()
    processor = trolleway_commons.CommonsOps()
    modelwiki = Model_wiki()
    helper_renamer = Helper_rename()

    wikidata= modelwiki.wikidata_input2id(args.wikidata)
    
    pagename=args.pagename
    csvpath=args.csv
    suffix = args.suffix
    prefix = args.prefix
    verify=args.verify
    set_sds = True
    
    if pagename is not None:
        new_name = helper_renamer.generate_filename(pagename,wikidata)
        new_name = helper_renamer.append_prefix(new_name,prefix)
        new_name = helper_renamer.append_suffix(new_name,suffix)
        rename_template_text = helper_renamer.generate_rename_template(new_name,rationale=args.rationale)
        
        mode = 'change'
        if mode=='change':
            if verify:
                print('prepend string')
                print(rename_template_text)
                print("Press Enter to continue or Ctrl+C for cancel...")
                input()
            helper_renamer.prepend_text_page(pagename,rename_template_text)
        
        if set_sds:
            entity_list = modelwiki.wikidata2instanceof_list(wikidata)
            entity_list.append(wikidata)
            modelwiki.append_image_descripts_claim(pagename,entity_list)
    elif csvpath is not None:
        with open(csvpath) as file:
            pageslist = file.read().splitlines()
            #pageslist = file.readlines()


        
        print('====== analysing changes ========')
        changeset=list()
        skipped=list()
        for el in pageslist:
            pagename=el
            try:
                new_name = helper_renamer.generate_filename(pagename,wikidata)
            except:
                print(pagename.ljust(20), ' error generate filename, skip')
                skipped.append(pagename)
                continue
            new_name = helper_renamer.append_prefix(new_name,prefix)
            new_name = helper_renamer.append_suffix(new_name,suffix)
            
            print(pagename.ljust(20),' ',new_name.ljust(30))
            changeset.append({'from':pagename,'to':new_name})
        print()
        print('====== proposed changes ========')
        for change in changeset:
            print(change['from'].ljust(70),' > ',change['to'].ljust(70))
        print(f'to change: {len(changeset)}   skipped: {len(skipped)}')
        verify = True
        if verify:
            print("Press Enter to continue or Ctrl+C for cancel...")
            input()
        
        for change in tqdm(changeset):
            rename_template_text = helper_renamer.generate_rename_template(change['to'],rationale=args.rationale)
            helper_renamer.prepend_text_page(change['from'],rename_template_text)
            if set_sds:
                entity_list = modelwiki.wikidata2instanceof_list(wikidata)
                entity_list.append(wikidata)
                modelwiki.append_image_descripts_claim(change['from'],entity_list)

    

    
        