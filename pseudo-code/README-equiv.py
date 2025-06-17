
class CQEToOursNewest:
    def __init__():
        pass

    def grab_CQE_daily():
        pass

    # TODO: more functions

if __name__ == "__main__":
    eachDay = CQEToOursNewest()
    eachDay.grab_CQE_daily() 
    """
    //pre-req before running this script: 
        - make sure "custom-top-cqe-bugs-daily-assigner" excel has 4 tabs 
                Tab 1 = Daily New; Tab 2 = GL; Tab 3 = NT; Tab 4 = PP

    ::Automated::

    (1) DATA SCRAPE CONDITIONED
    click on Chrome or Safari or Edge; open up tab 1 = excel cqe; 
    open up tab 2 = go into your microsoft hub and search for "custom-top-cqe-bugs-daily-assigner" excel

    (2) DATA PASTE 
    click back onto tab 1; grab CQE all content; filter column choices to copy --> click on tab 2 (custom excel)
    paste into existing sheet 1 of custom excel (columns 2::end);
        (if bug# exists already, then check priority number and replace priority # of current bug with this new priority number)

    (3) DROPDOWN TAG ASSIGNER
    copy existing last row that had 'drop down tag' then past on all leftmost column for new bugs;
    (reminder that this should be a "Data Validation:: List:: 3 option 'GL,NT,PP' dropdown tag)
    
    per each new row (remember where I pasted them (the row #, we know the column beg to end numberS)),
    auto-assign to GL/NT/PP based on failure mode type

    (4) REORDER by PRIORITY 
    check PRIORITY column per row. Reorder all
        - search for all from 1-100. if no rows have current 'priorty # to look at', skip to next priority number:
            Check on 1st most column (under Column Title names).
            
            If found, "add a new empty row" above 1st row (under Column Title names) 
            and paste full content of target row into that empty 1st row  (else keep and add 'current row num' by "+1")

            repeat each time. 
    
    (5) GRAB SPECIFIC NAME-LABEL ROWS TO RESPECTIVE TABS (titled the same abbrevation)
    copy all rows in full (all columns) if 1st column has label (like "GL"; ignore the '' empty options)
    
    (need to check last row in sheet (of GL/NT/PP tab) that had a column2 with data)
    paste into 2 rows below last row with filled content 

    repeat this for all sheets (tab 2, 3, 4)

    (6) Reorder priority of bugs per GL/NT/PP's sheet
        - run "REORDER BY PRIORTY" (step 4) again but per sheet.

    (7) DELETE COMPLETEDS
    add a last column on sheets 1-4 called "COMPELTEDS" (or if this column exists, then ignore this sub-step);
    In COMPLETEDS, see if empty cell or if cell is empty (no value) BUT highlighted in green
        - if green higlighted, then that is considered completed. remove that whole row's content of all columns. 
          delete that row itself physically;
    Do this for all sheets remaining

    (8) send email to geetha/nicolas/phuong saying 'Daily Top Bugs Ready For You to Start'
    - statement print-out in email body content saying you can click on rows you dont want and click to 'empty' 
        (on manual click, will have bug stay only in Tab#1)
    - copy-paste bugs with priority number 1-25 ONLY   into email body content  
        (3 paragraphs, 1 for GL, 1 for NT, 1 for PP)
    -send email 

    // additional
    - add Chron tab to run this python script every 9am morning for you. Just download this.
    """
