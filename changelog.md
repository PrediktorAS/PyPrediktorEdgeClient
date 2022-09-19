v0.9.3
- History read v/Aggregated items

v0.7.0
- Honeystore module added

v0.6.0
 - Flexible import of APISlibraries on win32. 

v0.5.0
- Added externalitem support
- Direct property access to modules
- Possibility to add new attributes to items
- Bug fixes
- Improved test-cases

v0.4.0
- Added a new hiveservice module with example code (incomplete)
- Update and improvements of existing examples
- Some points added to the 'to-do' list

v0.3.0
- Several changes to @Property for read-only
- Direct lookup on attribute.value from items. Allows such code as
```
t=myitem.Time
v=myItem.Value
otheritem.Value = 2*v
```
- Added some example modules
- Direct access to VQS from Hive
- Added some more attributes such as item_id
- Limiting exported symbols (all)
- Changed `type` to `module_type` to avoid conflicts with the resulved `type`
- Added module.add_item
- Added the possibility to write item-attr
- Item-attr understands enumerated values and returns the correct value.
- Some of the common features are moved to a separate util module. This will be nice when we introduce a honeystore module.
- Time conversion utilities .net DateTime <=> python datetime
- Quality class to deal with OPC-quality

v0.2.0
- Created the initial module from previous work by LH and DKG (AL)