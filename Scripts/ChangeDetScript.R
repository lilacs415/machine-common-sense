# Adrian Maries
# Convert .csv files exported by the Ruby script "Export.rb" into looking times.
# ------------------------------------------------------------------------------------------------------------------
# Set the working directory (where the R script is). The script assumes the input and output directories are inside.
# The input directory has to be named "InputFiles" and contain the .csv files output by the "Export.rb" script.
# The output directory has to be named "OutputFiles" and is where the script will output the looking times files.
library(tidyverse)

workingDir <- "/Users/gracesong/Desktop/Datavyu"
setwd(workingDir)


lookaway_criterion = c(1500, 2000, 2500, 3000)

time_until_first_look = 5000

# Get the file names of all files in the input directory.
inputFileList <- list.files(file.path(workingDir, "InputFiles"))

# Go through the files in the input directory to get the looking times from them.
for (fileName in inputFileList) {
  
  # Read the data from the current input file.
  changeDetData <- read.csv(file.path(workingDir, "InputFiles", fileName))
  
  # Get the trial list from the "Trials_ordinal" column and create vectors for storing the looking times.
  trialList <- unique(changeDetData$Trials_ordinal)
  trialType <- vector(mode = class(trialList), length = length(trialList))
  yLooksTotal <- vector(mode = class(trialList), length = length(trialList))
  nLooksTotal <- vector(mode = class(trialList), length = length(trialList))
  eLooksTotal <- vector(mode = class(trialList), length = length(trialList))
  yLooksBeforeLookaway <- matrix(ncol = length(lookaway_criterion), nrow = length(trialList))
  nLooksBeforeLookaway <- matrix(ncol = length(lookaway_criterion), nrow = length(trialList))
  eLooksBeforeLookaway <- matrix(ncol = length(lookaway_criterion), nrow = length(trialList))
  
  # Go through the trials and compute the corresponding looking times and add trial types.
  for (i in trialList) {
    
    trialType[i] = as.character(changeDetData$Trials_x[changeDetData$Trials_ordinal == trialList[i]][1])
    
    
    ## This part (ending in another ##) is pre-work to calculate looking time as time until the first criterion (e.g. 2sec) lookaway
    ## and also allow for 5sec for the infant to look
    
    
    # get looks away within all looks
    looks_away_on_trial = changeDetData$Looks_direction == "n" & changeDetData$Trials_ordinal == trialList[i] 
    
    # preallocate a bunch of trues, which will not be modified if we don't enter the if statement
    true_before_lookaway = rep(TRUE, length(looks_away_on_trial))
    
    # all lookaways in this trial
    nLooksDataFrameTotal <- changeDetData[looks_away_on_trial,]
    
    for (j in 1:length(lookaway_criterion)) {
      
      
      #  looks off that reached criterion
      criterion_looks_off = nLooksDataFrameTotal$Looks_offset - nLooksDataFrameTotal$Looks_onset > lookaway_criterion[j]
      
      # first look of this trial on or away?
      first_look_direction = changeDetData[changeDetData$Trials_ordinal == trialList[i] ,]$Looks_direction[1]
      
      # duration of first look
      first_look_duration = changeDetData[changeDetData$Trials_ordinal == trialList[i] ,]$Looks_offset[1] - 
        changeDetData[changeDetData$Trials_ordinal == trialList[i] ,]$Looks_onset[1]
      
      # set first lookaway to FALSE if it's the first thing in the trial but shorter than time_until_first_look 
      # (tolerance for time it takes infant to look)
      if (first_look_direction == 'n' & first_look_duration < time_until_first_look) {
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
      
      # Lookaway time before criterion lookaway has been reached
      nLooksDataFrameBeforeLookaway <- changeDetData[looks_away_on_trial & true_before_lookaway,]
      nLooksBeforeLookaway[i, j] <- sum(nLooksDataFrameBeforeLookaway$Looks_offset - nLooksDataFrameBeforeLookaway$Looks_onset)
      
      # Looking time before criterion lookaway has been reached
      yLooksDataFrameBeforeLookaway <- changeDetData[changeDetData$Looks_direction == "y" & changeDetData$Trials_ordinal == trialList[i] & true_before_lookaway,]
      yLooksBeforeLookaway[i, j] <- sum(yLooksDataFrameBeforeLookaway$Looks_offset - yLooksDataFrameBeforeLookaway$Looks_onset)
      
      # Error looks before criterion lookaway has been reached
      eLooksDataFrameBeforeLookaway <- changeDetData[changeDetData$Looks_direction == "e" & changeDetData$Trials_ordinal == trialList[i] & true_before_lookaway,]
      eLooksBeforeLookaway[i, j] <- sum(eLooksDataFrameBeforeLookaway$Looks_offset - eLooksDataFrameBeforeLookaway$Looks_onset)
      
    }
    
    ##  lookaways, looking times and error looks across whole trial
    
    # Total lookaway time
    nLooksDataFrameTotal <- changeDetData[looks_away_on_trial,]
    nLooksTotal[i] <- sum(nLooksDataFrameTotal$Looks_offset - nLooksDataFrameTotal$Looks_onset)
    
    # Total looking time
    yLooksDataFrameTotal <- changeDetData[changeDetData$Looks_direction == "y" & changeDetData$Trials_ordinal == trialList[i],]
    yLooksTotal[i] <- sum(yLooksDataFrameTotal$Looks_offset - yLooksDataFrameTotal$Looks_onset)
    
    # Total error looks
    eLooksDataFrameTotal <- changeDetData[changeDetData$Looks_direction == "e" & changeDetData$Trials_ordinal == trialList[i],]
    eLooksTotal[i] <- sum(eLooksDataFrameTotal$Looks_offset - eLooksDataFrameTotal$Looks_onset)
  }
  
  # Create a data frame with the looking times and write it to the output folder.
  outputDataFrame <- data.frame(trialList, trialType, yLooksTotal / 1000, nLooksTotal / 1000, eLooksTotal / 1000)
  names(outputDataFrame) <- c("Trial Number", "Trial Type", "Looks On Total (s)", "Looks Off Total (s)", "Looks Error Total (s)")
  
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
  outputFileName <- str_replace(fileName, 'verbose', 'data')
  write.csv(outputDataFrame, file.path(workingDir, "OutputFiles", outputFileName))
}