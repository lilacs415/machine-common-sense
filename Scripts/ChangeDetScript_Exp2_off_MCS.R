# Adrian Maries
# Convert .csv files exported by the Ruby script "Export.rb" into looking times.
# ------------------------------------------------------------------------------------------------------------------
# Set the working directory (where the R script is). The script assumes the input and output directories are inside.
# The input directory has to be named "InputFiles" and contain the .csv files output by the "Export.rb" script.
# The output directory has to be named "OutputFiles" and is where the script will output the looking times files.
library(tidyverse)
library(zoo)

workingDir <- "/Users/gracesong/Desktop/Datavyu"
setwd(workingDir)

lookaway_criterion = c(1500, 2000, 2500, 3000)

time_until_first_look = 5000


# Get the file names of all files in the input directory.
inputFileList <- list.files(file.path(workingDir, "InputFiles"))

# Go through the files in the input directory to get the looking times from them.
for (fileName in inputFileList) {
  
  print(fileName)
  
  # Read the data from the current input file.
  changeDetData <- read.csv(file.path(workingDir, "InputFiles", fileName))
  
  # Get the trial list from the "Trials_ordinal" column and create vectors for storing the looking times.
  trialList <- changeDetData %>% select(Trials.ordinal) %>% filter(!is.na(Trials.ordinal)) %>% pull() + 1
  looksList <- changeDetData %>% select(Looks.ordinal) %>% filter(!is.na(Looks.ordinal)) %>% pull() + 1
  
  trialType <- vector(mode = class(trialList), length = length(trialList))
  trialIdx <- vector(mode = class(looksList), length = length(looksList))
  yLooksTotal <- vector(mode = class(trialList), length = length(trialList))
  nLooksTotal <- vector(mode = class(trialList), length = length(trialList))
  eLooksTotal <- vector(mode = class(trialList), length = length(trialList))
  yLooksBeforeLookaway <- matrix(ncol = length(lookaway_criterion), nrow = length(trialList))
  nLooksBeforeLookaway <- matrix(ncol = length(lookaway_criterion), nrow = length(trialList))
  eLooksBeforeLookaway <- matrix(ncol = length(lookaway_criterion), nrow = length(trialList))
  
  # go from export format to expanded format
  
  # figure out which trials the look times fit into
  for (i in looksList) {
    trialIdx[i] = trialList[na.trim(changeDetData$Trials.offset) >= changeDetData$Looks.offset[i] & na.trim(changeDetData$Trials.onset) <= changeDetData$Looks.onset[i]][1]
    
    if (is.na(trialIdx[i])) { # if there's an NA above its because there was an offlook going beyond trial boundaries, set to offset of trial
      changeDetData$Looks.offset[i] = changeDetData$Trials.offset[sum(changeDetData$Looks.offset[i] > changeDetData$Trials.offset, na.rm = TRUE)]
      trialIdx[i] = trialList[na.trim(changeDetData$Trials.offset) >= changeDetData$Looks.offset[i] & na.trim(changeDetData$Trials.onset) <= changeDetData$Looks.onset[i]][1]
      
      }
    }
  
  changeDetData$Trials_offset = changeDetData$Trials.offset[trialIdx]
  changeDetData$Trials_onset = changeDetData$Trials.onset[trialIdx]
  changeDetData$Trials_ordinal = changeDetData$Trials.ordinal[trialIdx] + 1
  changeDetData$trial_type = changeDetData$Trials.x[trialIdx]
  changeDetData$ID_session = changeDetData$ID.session[1]
  
  # Go through the trials and compute the corresponding looking times and add trial types.
  for (i in trialList) {
    print(i)
    
    trialType[i] = as.character(changeDetData$trial_type[changeDetData$Trials_ordinal == trialList[i]][1])
    
    ## This part (ending in another ##) is pre-work to calculate looking time as time until the first criterion (e.g. 2sec) lookaway
    ## and also allow for 5sec for the infant to look
    
    # get looks away within all looks
    looks_away_on_trial = changeDetData$Looks.direction == 'off' & changeDetData$Trials_ordinal == trialList[i] 
    error_looks_on_trial = changeDetData$Looks.direction == "e" & changeDetData$Trials_ordinal == trialList[i] 
    
    # preallocate a bunch of trues, which will not be modified if we don't enter the if statement
    true_before_lookaway = rep(TRUE, length(looks_away_on_trial))
    
    # all lookaways in this trial
    nLooksDataFrameTotal <- changeDetData[looks_away_on_trial,]
    eLooksDataFrameTotal <- changeDetData[error_looks_on_trial,]
    
    for (j in 1:length(lookaway_criterion)) {
      
      #  looks off that reached criterion
      criterion_looks_off = nLooksDataFrameTotal$Looks.offset - nLooksDataFrameTotal$Looks.onset > lookaway_criterion[j]
      
      # first look of this trial on or away?
      first_look_direction = changeDetData[changeDetData$Trials_ordinal == trialList[i] ,]$Looks.direction[1]
      
      # duration of first look
      first_look_duration = changeDetData[changeDetData$Trials_ordinal == trialList[i] ,]$Looks.offset[1] - 
        changeDetData[changeDetData$Trials_ordinal == trialList[i] ,]$Looks.onset[1]
      
      # check if there were any off looks
      any_off_looks = nrow(nLooksDataFrameTotal) > 0  
      any_error_looks = nrow(eLooksDataFrameTotal) > 0  
      
      # set first lookaway to FALSE if it's the first thing in the trial but shorter than time_until_first_look 
      # (tolerance for time it takes infant to look)
      if (any_off_looks & first_look_direction == 'off' & first_look_duration < time_until_first_look) {
        criterion_looks_off[1] = FALSE
      }
      
      if (any(criterion_looks_off)) { 
        
        # get index of first look away within lookaways
        first_lookaway = which(criterion_looks_off == TRUE)[1] 
        
        # get index of first lookaway within all looks
        first_lookaway_on_trial = which(looks_away_on_trial == TRUE)[first_lookaway] 
        
        # construct logical vector to terminate sum before first lookaway
        true_before_lookaway = c(rep(TRUE, first_lookaway_on_trial), rep(FALSE, length(looks_away_on_trial)-first_lookaway_on_trial)) 
        
      }
      
      # if there are no lookaways and error looks
      if (!any_off_looks & !any_error_looks) {
        nLooksBeforeLookaway[i, j] = 0
        eLooksBeforeLookaway[i, j] = 0
        yLooksBeforeLookaway[i, j] = changeDetData[i,]$Trials.offset - changeDetData[i,]$Trials.onset
        
      }
      else {
        # Lookaway time before criterion lookaway has been reached
        nLooksDataFrameBeforeLookaway <- changeDetData[looks_away_on_trial & true_before_lookaway,]
        nLooksBeforeLookaway[i, j] <- sum(nLooksDataFrameBeforeLookaway$Looks.offset - nLooksDataFrameBeforeLookaway$Looks.onset)
        
        DataFrameBeforeLookaway = changeDetData[true_before_lookaway & changeDetData$Trials_ordinal == trialList[i], ]
        
        # Looking time before criterion lookaway has been reached
        trial_duration = DataFrameBeforeLookaway$Trials_offset - DataFrameBeforeLookaway$Trials_onset
        yLooksBeforeLookaway[i, j] <- trial_duration[1] - nLooksBeforeLookaway[i, j]
        
        # Error looks before criterion lookaway has been reached
        eLooksDataFrameBeforeLookaway <- DataFrameBeforeLookaway[changeDetData$Looks.direction == "e",]
        eLooksBeforeLookaway[i, j] <- sum(eLooksDataFrameBeforeLookaway$Looks.offset - eLooksDataFrameBeforeLookaway$Looks.onset)
        
      }
        
      }

    
    ##  lookaways, looking times and error looks across whole trial
    
    if (!any_off_looks & !any_error_looks) {
      nLooksTotal[i] = 0
      eLooksTotal[i]  = 0
      yLooksTotal[i] = changeDetData[i,]$Trials.offset - changeDetData[i,]$Trials.onset
      trialType[i] = as.character(changeDetData[i,]$trial_type)
    }
    else {
    
    # Total lookaway time
    nLooksDataFrameTotal <- changeDetData[looks_away_on_trial,]
    nLooksTotal[i] <- sum(nLooksDataFrameTotal$Looks.offset - nLooksDataFrameTotal$Looks.onset)
    
    # Total looking time
    trial_duration = changeDetData[changeDetData$Trials_ordinal == trialList[i],]$Trials_offset - 
      changeDetData[changeDetData$Trials_ordinal == trialList[i],]$Trials_onset
    
    yLooksTotal[i] <- trial_duration[1] - nLooksTotal[i]
    
    # Total error looks
    eLooksDataFrameTotal <- changeDetData[changeDetData$Looks.direction == "e" & changeDetData$Trials_ordinal == trialList[i],]
    eLooksTotal[i] <- sum(eLooksDataFrameTotal$Looks.offset - eLooksDataFrameTotal$Looks.onset)
    }
  }
  
  
  # Create a data frame with the looking times and write it to the output folder.
  outputDataFrame <- data.frame(rep(changeDetData$ID_session[1], length(trialList)), trialList, trialType, yLooksTotal / 1000, nLooksTotal / 1000, eLooksTotal / 1000)
  names(outputDataFrame) <- c("Session Number", "Trial Number", "Trial Type", "Looks On Total (s)", "Looks Off Total (s)", "Looks Error Total (s)")
  
  for (i in 1:length(lookaway_criterion)) {
    outputDataFrame <- cbind(outputDataFrame, yLooksBeforeLookaway[,i]/1000)
    outputDataFrame <- cbind(outputDataFrame, nLooksBeforeLookaway[,i]/1000)
    outputDataFrame <- cbind(outputDataFrame, eLooksBeforeLookaway[,i]/1000)
    
    # rename last three
    names(outputDataFrame)[(length(names(outputDataFrame))-2):length(names(outputDataFrame))] <- c(sprintf("Looks On %d (s)", lookaway_criterion[i]),
                                                                                                   sprintf("Looks Off %d (s)", lookaway_criterion[i]),
                                                                                                   sprintf("Looks Error %d (s)", lookaway_criterion[i])
    )
  }
  
  outputFileName <- fileName %>% str_replace('verbose', 'data')
  write.csv(outputDataFrame, file.path(workingDir, "OutputFiles", outputFileName))
}

