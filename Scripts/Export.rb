# Print single-cell columns "T" as repeated columns for file.
# Iterate over nested cells.
# For each nested cell "N", iterate over list of "sequential columns" and
# print rows of data for each cell "S" in that column nested inside "N".
# For example (Ci is the ith code in the cell):
# row1 : T1C1, T1C2, T2C1, N1C1, N2C1, N2C2, S1C1, S1C2, <blank>, <blank>
# row2 : T1C1, T1C2, T2C1, N1C1, N2C1, N2C2, S1C1, S1C2, <blank>, <blank>
# row3 : T1C1, T1C2, T2C1, N1C1, N2C1, N2C2, <blank>, <blank>, S2C1, S2C2

## Parameters
# input_folder = '~/Desktop/Datavyu’
# output_file = '~/Desktop/Data.csv'

input_folder = '/Users/gracesong/Desktop/Datavyu/Datavyu2'
output_file = '/Users/gracesong/Desktop/Datavyu/Datavyu2/data/data.csv'
code_map = {
  'ID' => %w(sub dot dob sex),
  'Trials' => %w(x ordinal onset offset),
  'Looks' => %w(ordinal onset offset direction)
}
static_columns = %w(ID)
nested_columns = %w(Trials Looks)
sequential_columns = %w()
blank_value = '' # code to put in for missing cells
delimiter = ','

# Set to true to force a row to be printed for each innermost-nested cell.
# Default behavior is to skip nested cells that don't have any data for sequential cells.
ensure_rows_per_nested_cell = true

## Body
require 'Datavyu_API.rb'

# Patch for backwards compatibility with v1.3.4
alias :get_column :getColumn unless respond_to? :get_column
unless RCell.methods.include?(:get_codes)
  unless self.respond_to?(:get_codes)
    # Map the specified code names to their values.
    # If no names specified, use self.arglist.
    # @note Onset, offset, and ordinal are returned as Integers; all else are Strings
    # @param codes [Array<String>] (optional): Names of codes.
    # @return [Array] Values of specified codes.
    def get_codes(*codes)
      codes = self.arglist if codes.nil? || codes.empty?
      codes.flatten!

      vals = codes.map do |cname|
        case(cname)
        when 'onset'
          self.onset
        when 'offset'
          self.offset
        when 'ordinal'
          self.ordinal
        else
          @arglist.include?(cname)? self.get_arg(cname) : raise("Failed to get the following code from cell #{self.ordinal} in column #{self.parent}: #{cname}")
        end
      end

      return vals
    end
  end
end

data = []
# Header order is: static, nested, sequential
header = (static_columns + nested_columns + sequential_columns).map do |colname|
  code_map[colname].map{ |codename| "#{colname}_#{codename}" }
end
header.flatten!
data << header.join(delimiter)

# Init arrays of default values.
default_data = {}
code_map.each_pair{ |k, v| default_data[k] = [blank_value] * v.size }

input_path = File.expand_path(input_folder)
infiles = Dir.chdir(input_path){ Dir.glob('**/*.opf') }

infiles.each do |infile|
  $db, $pj = load_db(File.join(input_path, infile))

  puts "Printing #{infile}..."

  columns = {}
  code_map.keys.each{ |x| columns[x] = get_column(x) }

  # Get static data from first cells.
  static_data = static_columns.map do |colname|
    col = columns[colname]
    cell = col.cells.first
    raise "Can't find cell in #{colname}" if cell.nil? # static columns must contain cell

    cell.get_codes(code_map[colname])
  end
  static_data.flatten!

  # Iterate over cells of innermost-nested column.
  if(nested_columns.empty?)
    inner_data = []
    outer_data = []

    # Iterate over sequential columns.
    rows_added = 0
    sequential_columns.each do |scol|
      # Reset data hash so values are not carried over.
      seq_data = default_data.select{ |k, v| sequential_columns.include?(k) }

      # Iterate over sequential cells nested inside inner cell.
      seq_cells = columns[scol].cells
      seq_cells.each do |scell|
        seq_data[scol] = scell.get_codes(code_map[scol])

        row = static_data + outer_data + inner_data + seq_data.values.flatten
        data << row.join(delimiter)
        rows_added += 1
      end
    end
  else
    inner_col = nested_columns.last
    outer_cols = nested_columns[0..-2]
    columns[inner_col].cells.each do |icell|
      inner_data = icell.get_codes(code_map[inner_col])
      outer_data = outer_cols.map do |ocol|
        ocell = columns[ocol].cells.find{ |x| x.contains(icell) }
        raise "Can't find nesting cell in column #{ocol} for cell #{icell.ordinal} in column #{inner_col}." if ocell.nil?
        ocell.get_codes(code_map[ocol])
      end
      outer_data.flatten!

      # Init blank data hash so that data for this column is placed properly.
      seq_data = default_data.select{ |k, v| sequential_columns.include?(k) }

      # Iterate over sequential columns.
      rows_added = 0
      sequential_columns.each do |scol|
        # Reset data hash so values are not carried over.
        seq_data = default_data.select{ |k, v| sequential_columns.include?(k) }

        # Iterate over sequential cells nested inside inner cell.
        seq_cells = columns[scol].cells.select{ |x| icell.contains(x) }
        seq_cells.each do |scell|
          seq_data[scol] = scell.get_codes(code_map[scol])

          row = static_data + outer_data + inner_data + seq_data.values.flatten
          data << row.join(delimiter)
          rows_added += 1
        end
      end

      # Edge case for no nested sequential cell(s).
      if(rows_added == 0 && ensure_rows_per_nested_cell)
        row = static_data + outer_data + inner_data + seq_data.values.flatten
        data << row.join(delimiter)
        rows_added +=1
      end
    end
  end
end

puts "Writing data to file..."
outfile = File.open(File.expand_path(output_file), 'w+')
outfile.puts data
outfile.close

puts "Finished."
