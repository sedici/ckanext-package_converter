from ckan.lib.helpers import dataset_display_name
from ckanext.package_converter.model.scheming_converter import Datacite31SchemingConverter
from pylons import config
from xmltodict import unparse
import ckan.plugins.toolkit as toolkit
import collections

class DefaultCKANDatacite31SchemingConverter(Datacite31SchemingConverter):
    """Converts datasets schema in a default instance of CKAN to Datacite Schema"""
    def __init__(self):
        super(DefaultCKANDatacite31SchemingConverter, self).__init__()

    def _datacite_converter_schema(self, dataset_dict):
        datacite_dict = collections.OrderedDict()

        # Identifier
        # CKAN default metadata dataset has no DOI, then the Datacite identifier is no defined...

        # Header
        datacite_dict['resource']=collections.OrderedDict()
        datacite_dict['resource']['@xsi:schemaLocation'] = '{namespace} {schema}'.format(namespace=self.output_format.get_namespace(),
                                                                                         schema=self.output_format.get_xsd_url())
        datacite_dict['resource']['@xmlns']='{namespace}'.format(namespace=self.output_format.get_namespace())
        datacite_dict['resource']['@xmlns:xsi']='http://www.w3.org/2001/XMLSchema-instance'

        # Title
        if self._is_defined_metadata('title', dataset_dict):
            datacite_titles_tag = 'titles'
            datacite_title_tag = 'title'
            datacite_dict['resource'][datacite_titles_tag] = { datacite_title_tag: [ ] }
            datacite_dict['resource'][datacite_titles_tag][datacite_title_tag] += [ {'#text': dataset_dict['title']}]

        # PublicationYear
        if self._is_defined_metadata('metadata_created', dataset_dict):
            # Publication year*
            datacite_publication_year_tag = 'publicationYear'
            datacite_dict['resource'][datacite_publication_year_tag] = {'#text': dataset_dict['metadata_created'] }

        #Creators
        #For CKAN there is only one creator
        if self._is_defined_metadata('author', dataset_dict):
            datacite_creators_tag = 'creators'
            datacite_creator_tag = 'creator'
            datacite_dict['resource'][datacite_creators_tag] = { datacite_creator_tag: [ ] }
            datacite_creator = collections.OrderedDict()
            datacite_creator['creatorName'] = {'#text': dataset_dict['author']}
            datacite_dict['resource'][datacite_creators_tag][datacite_creator_tag] += [ datacite_creator ]

        # Subjects
        if self._is_defined_metadata('tags', dataset_dict):
            datacite_subjects_tag = 'subjects'
            datacite_subject_tag = 'subject'
            datacite_subjects = []
            for tag in dataset_dict['tags']:
                # Every tag is a dictionary inself
                tag_name = tag.get('display_name', tag.get('name',''))
                datacite_subjects += [{ '#text':tag_name}]
            datacite_dict['resource'][datacite_subjects_tag] = { datacite_subject_tag: datacite_subjects }

        # Contributor (contact person)
        if self._is_defined_metadata('manteiner', dataset_dict):
            datacite_contributors_tag = 'contributors'
            datacite_contributor_tag = 'contributor'
            datacite_contributors = []
            datacite_contributor = collections.OrderedDict()
            datacite_contributor['contributorName'] = {'#text': dataset_dict['manteiner']}
            datacite_contributors += [ datacite_contributor ]
            datacite_dict['resource'][datacite_contributors_tag] = { datacite_contributor_tag: datacite_contributors }

        # Language
        # By default, the ckan datasets has no language in metadata fields
        datacite_language_tag = 'language'
        default_ckan_language = config.get('ckan.locale_default','en')
        datacite_dict['resource'][datacite_language_tag] = {'#text': default_ckan_language }

        # Sizes (not defined in scheming, taken from default CKAN resource)
        datacite_size_group_tag = 'sizes'
        datacite_size_tag = 'size'
        datacite_sizes = []
        for resource in dataset_dict.get('resources', []):
            if resource.get('size', ''):
                datacite_sizes += [{'#text': str(resource.get('size', ' ')) + ' bytes'}]
        if datacite_sizes:
             datacite_dict['resource'][datacite_size_group_tag] = {datacite_size_tag: datacite_sizes}

        # Formats (get from resources)
        datacite_format_group_tag = 'formats'
        datacite_format_tag = 'format'
        datacite_formats = []

        for resource in dataset_dict.get('resources', []):
          resource_format = resource.get('mimetype', resource.get('mimetype_inner', ''))
          if resource_format:
              datacite_format = {'#text': resource_format}
              if datacite_format not in datacite_formats:
                  datacite_formats += [datacite_format]
        if datacite_formats:
            datacite_dict['resource'][datacite_format_group_tag] = {datacite_format_tag: datacite_formats}

        # Version
        if self._is_defined_metadata('version',dataset_dict):
            datacite_version_tag = 'version'
            datacite_dict['resource'][datacite_version_tag] = {'#text': dataset_dict['version'] }

        # Alternate Identifier (CKAN URL)
        ckan_package_url = config.get('ckan.site_url','') + toolkit.url_for(controller='package', action='read', id=dataset_dict.get('name', ''))
        datacite_dict['resource']['alternateIdentifiers']={'alternateIdentifier':[{'#text':ckan_package_url, '@alternateIdentifierType':'URL'}]}

         # Rights
        if self._is_defined_metadata('license_title', dataset_dict) and self._is_defined_metadata('license_url', dataset_dict):
            datacite_rights_group_tag = 'rightsList'
            datacite_rights_tag = 'rights'
            datacite_rights_uri_tag = 'rightsURI'
            datacite_rights_item = { '#text': dataset_dict['license_title'], '@'+ datacite_rights_uri_tag : dataset_dict['license_url']}
            datacite_dict['resource'][datacite_rights_group_tag] = {datacite_rights_tag: [datacite_rights_item] }

        # Description (Abstract)
        if self._is_defined_metadata('note',dataset_dict):
            datacite_descriptions_tag = 'descriptions'
            datacite_description_tag = 'description'
            datacite_description = {'#text': dataset_dict['notes'], '@descriptionType': 'Abstract'}
            datacite_dict['resource'][datacite_descriptions_tag] = { datacite_description_tag: [datacite_description] }

        # Convert to xml
        converted_package = unparse(datacite_dict, pretty=True)

        return converted_package

    def _is_defined_metadata(self, metadata_name, dataset_dict):
        """
        Check if metadata_name exists in metadata dataset and if is not empty value
        If metadata is a list, this methods check if is empty too.
        """
        return (metadata_name in dataset_dict and dataset_dict[metadata_name])