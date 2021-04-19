xgettext --files-from files.in --from-code utf-8 --add-comments --output messages.pot

for locale in */; do
	file="$locale/LC_MESSAGES/boribay"

	msgmerge --update --no-fuzzy-matching --backup off "$file.po" messages.pot

	msgfmt "$file.po" --output-file "$file.mo"; done
