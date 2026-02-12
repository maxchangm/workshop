"""
RAG Workshop Corpus - S17 IT Security Policy (Docling Hybrid Chunker)

Extracted from Hong Kong Government S17_EN.pdf (Version 8.2, April 2025)
- Docling HybridChunker with max_tokens=512
- Filtered: Removed TOC, amendment history, images, short chunks
- Original: 144 chunks → Final: 80 chunks

TUNED TEST QUESTIONS (v2):
These questions match actual S17 policy content for clearer search differentiation.
Each question has a specific correct document with implementation details (not just mentions).
"""

documents = [
    # Chunk 0: COPYRIGHT NOTICE - FILLER
    "Version 8.2 April 2025 © The Government of the Hong Kong Special Administrative Region of the People's Republic of China The contents of this document remain the property of and may not be reproduced in whole or in part without the express permission of the Government of the Hong Kong Special Administrative Region of the People's Republic of China.",
    # Chunk 1: Purpose/Scope - Overview
    "With the effective use of Internet services and the general adoption of cloud and mobile computing, the security and survivability of information systems are essential to the economy and society. Our increasing dependence on IT for office works and public services delivery has brought new business focus that the key information systems and data we rely on have to be secure and actively protected for the smooth operations of all government bureaux and departments (B/Ds), underpinning public confidence, security and privacy are fundamental to the effective, efficient and safe conduct of government business.",
    # Chunk 2: Policy Overview - Lists 14 areas
    "This document adopts and adapts the security areas and controls specified in the Information security, cybersecurity and privacy protection - Information security management systems - Requirements (ISO/IEC 27001: 2022) and the Information security, cybersecurity and privacy protection - Information security controls (ISO/IEC 27002: 2022) published by the International Organization for Standardization (ISO) and the International Electrotechnical Commission (IEC). This document addresses the mandatory security considerations in the following 14 areas: Management responsibilities; IT security policies; Human resource security; Asset management; Access control; Cryptography; Physical and environmental security; Operations security; Communications security; System acquisition, development and maintenance; Outsourcing security; Security incident management; IT security aspects of business continuity management; and Compliance.",
    # Chunk 3: Conventions
    "The following is a list of conventions used in this document. Shall = The use of the word 'shall' indicates a mandatory requirement. Should = The use of the word 'should' indicates a best practice, which should be implemented whenever possible. May = The use of the word 'may' indicates a desirable best practice.",
    # Chunk 4: Security Framework Overview
    "To co-ordinate and promote IT security in the Government, an Information Security Management Framework comprising the following five parties has been established: Information Security Management Committee (ISMC); IT Security Working Group (ITSWG); Government Information Security Incident Response Office (GIRO); Government Computer Emergency Response Team Hong Kong (GovCERT.HK); and Bureaux/Departments.",
    # Chunk 5: Central vs Departmental
    "Government Information Security Management Organisation Structure. The Government Information Security Management Committee (ISMC) and the Information Security Management Structure within Bureaux/Departments.",
    # Chunk 6: ISMC Role
    "The ISMC is chaired by the Government Chief Information Officer (GCIO) who is also the Chairman of the Digital Policy Office (DPO). The ISMC has the following major functions: Advise on government information security policies; Endorse IT security guidelines; Review major IT security incidents; and Promote security awareness.",
    # Chunk 7: ITSWG Role
    "The IT Security Working Group (ITSWG) was established in May 2000, and its responsibilities are to: Co-ordinate activities aiming at enhancing the Government IT security; and Follow up matters as instructed by the ISMC.",
    # Chunk 8: GovCERT Role
    "The Government Computer Emergency Response Team Hong Kong (GovCERT.HK) was established in April 2015. In addition to collaborating with GIRO Standing Office in co-ordinating information and cyber security incident handling for the Government, GovCERT.HK also works closely with the Hong Kong Computer Emergency Response Team Coordination Centre (HKCERT) to monitor cyber security attacks, provide early warnings, and respond to information security incidents in the Government.",
    # Chunk 9: Definitions - FILLER
    "j), Staff = A collective term used to describe all personnel employed or whose service is acquired to work for the Government, including all public officers irrespective of the employment period and terms, non-government secondees engaged to work in the Government, consultants and contractors engaged by the Government to perform duties.",
    # Chunk 10: DSO Role
    "The Head of B/D will designate a Departmental Security Officer (DSO) to perform the departmental security related duties. The DSO will take the role of an executive to: Discharge responsibilities for all aspects of security for the B/D; and Advise on the set up and review of the security policy. The DSO may take on the role of the DITSO.",
    # Chunk 11: GIRO Framework
    "Response GIRO. To co-ordinate and promote IT security in the Government, an Information Security Management Framework comprising the following five parties has been established: Information Security Management Committee (ISMC); IT Security Working Group (ITSWG); Government Information Security Incident Response Office (GIRO); Government Computer Emergency Response Team Hong Kong (GovCERT.HK); and Bureaux/Departments.",
    # Chunk 12: ISIRT and GIRO - CORRECT for incident question
    "To handle information security incidents occurring in B/Ds, an Information Security Incident Response Team (ISIRT) shall be established in each B/D. The Government Information Security Incident Response Office (GIRO) provides central coordination and support to the operation of individual ISIRTs of B/Ds. The GIRO Standing Office serves as the executive arm of GIRO. The GIRO has the following major functions: Maintain a central inventory and oversee the handling of all information security incidents in the Government; Prepare periodic statistics reports on government information security incidents; Act as a central office to co-ordinate the handling of multiple-point security attacks; and Enable experience sharing and information exchange related to information security incident handling among ISIRTs of different B/Ds.",
    # Chunk 13: B/D Responsibilities
    "Unit B/Ds shall be responsible for the security protection of their information assets and information systems. The roles and responsibilities of IT security staff within a B/D are detailed in Section 5.2 - Departmental IT Security Organisation.",
    # Chunk 14: Security Principles
    "Core Security Principles. Protection of information while being processed, in transit, and in storage. Security measures shall be considered and implemented as appropriate to preserve the confidentiality, integrity, and availability of Government information assets and information systems.",
    # Chunk 15: DITSO Appointment - CORRECT for DITSO question
    "Head of B/D shall appoint an officer at D3 level or above from the senior management to be the Departmental IT Security Officer (DITSO) and responsible for IT security. As the senior management of the B/D, the DITSO shall participate in the overall steering of IT security matters of the B/D. The DITSO shall also understand the B/D's priorities, the importance of the B/D's information systems and data assets, and the level of security that shall be achieved. If a B/D does not have a directorate officer at D3 level or above, the highest rank directorate officer of the B/D shall assume the position of DITSO so as to uphold the principle of ensuring accountability in IT security.",
    # Chunk 16: DITSO Responsibilities
    "SB and DPO will provide training to DITSOs to facilitate them in carrying out their duties and DITSOs shall attend the designated training. The roles and responsibilities of DITSO shall be clearly defined, which include but are not limited to the following: Establish and maintain an information protection program; Establish a proper security governance process; Identify and manage IT security risks; Define security requirements for information systems under development or procurement; and Report information security incidents to GIRO.",
    # Chunk 17: Senior Management
    "The senior management of B/Ds shall have an appreciation of IT security, its problems and resolutions. Senior management should consider setting up of an information security steering committee which should meet on a regular basis to review and discuss security matters.",
    # Chunk 18: DSO/DITSO Collaboration
    "The Head of B/D will designate a Departmental Security Officer (DSO) to perform the departmental security related duties. The DSO may take on the role of the DITSO. Alternatively, in those B/Ds where someone else is appointed, the DITSO shall collaborate with the DSO to oversee the IT security of the B/D.",
    # Chunk 19: Security Governance
    "General Management and Security Risk Management. B/Ds shall develop, document, implement, maintain and review appropriate security measures to protect their information systems and data assets.",
    # Chunk 20: IT Security Management Unit
    "B/Ds shall establish an IT security management unit which reports to DITSO and assists DITSO in discharging his/her duties. The size and composition of an IT security management unit shall be commensurate with the size, complexity and criticality of the B/D's information systems.",
    # Chunk 21: IT Security Administrators
    "IT Security Administrators shall be responsible for providing security and risk management related support services. His/her responsibilities also include: Assist in identifying and mitigating system vulnerabilities; and Monitor threat intelligence sources and stay updated on emerging security threats.",
    # Chunk 22: LAN/System Administrators
    "LAN/System Administrators shall be responsible for the day-to-day administration, operation and configuration of the computer systems and network in B/Ds, whereas Internet System Administrators are responsible for the Internet connection.",
    # Chunk 23: ISIRT Commander
    "Departmental Information Security Incident Response Team (ISIRT) Commander. The ISIRT is the central focal point for co-ordinating the handling of information security incidents occurring within the respective B/D. The Head of B/D should designate an officer from the senior management to be the ISIRT Commander.",
    # Chunk 24: ISIRT Responsibilities
    "The responsibilities of an ISIRT Commander include: Provide overall supervision and co-ordination of information security incident handling; Make decisions on critical matters such as damage containment and system recovery; Trigger the departmental disaster recovery procedure where appropriate; and Collaborate with GIRO in reporting information security incidents.",
    # Chunk 25: Security Principles Detail
    "In general, an external system shall be assumed to be insecure. When B/Ds' information assets or information systems connect with external systems, B/Ds should ensure the connection is secured by means of appropriate technical solutions such as firewalls or virtual private network (VPN) systems, and the connection is authorised by the appropriate management authority of the B/D.",
    # Chunk 26: Security Objectives
    "The security of Government information systems and data assets shall be achieved through: Protection of information while being processed, in transit, and in storage; and Security measures commensurate with the determined risks.",
    # Chunk 27: Management Direction
    "Management Direction for IT Security. B/Ds shall ensure that appropriate security measures are implemented as detailed in this document. B/Ds shall ensure regular review on continuing suitability, adequacy and effectiveness of the security measures.",
    # Chunk 28: Human Resource Security
    "Human Resource Security. B/Ds shall ensure that employees and contractors meet security requirements, understand their responsibilities, and are suitable for their roles throughout their employment lifecycle.",
    # Chunk 29: New Employment
    "New, During or Termination of Employment. B/Ds shall advise all staff of their IT security responsibilities upon being assigned a new post and periodically throughout their term of employment. Information security is the responsibility of every member of the staff in the Government. Staff shall receive appropriate awareness training and regular updates on the IT Security Policy.",
    # Chunk 30: Asset Management
    "Asset Management. B/Ds shall ensure that an inventory of information systems, hardware assets, software assets, valid warranties, service agreements and legal/contractual documents are properly owned, kept and maintained.",
    # Chunk 31: Information Classification
    "Information Classification. B/Ds shall comply with the government security requirements in relation to information classification, labelling and handling. All classified information shall be encrypted in storage irrespective of the storage media.",
    # Chunk 32: Storage Media Handling
    "Storage Media Handling. B/Ds shall protect information stored on storage media through the application of appropriate security measures including classification, labelling, and access control.",
    # Chunk 33: Access Control Introduction
    "Access Control. B/Ds shall prevent unauthorised user access and compromise of information systems and assets and allow only authorised computer resources to connect to the government internal network.",
    # Chunk 34: User Access Management
    "User Access Management. Procedures for approving, granting and managing user access, including user registration/de-registration, password delivery and password reset, shall be documented.",
    # Chunk 35: Password Management
    "Passwords shall not be shared or divulged unless necessary. Passwords shall be changed on a regular basis and whenever there is any indication of possible compromise or leakage. Passwords should contain a mixture of alphabetic and numeric characters. Passwords should not be related to personal information such as names of family members, birth dates or telephone numbers.",
    # Chunk 36: System Access Control
    "System and Application Access Control. Authentication shall be performed in a manner commensurate with the sensitivity of the information to be accessed. Consecutive unsuccessful authentication attempts shall be limited to a defined threshold, which should normally not exceed five.",
    # Chunk 37: Mobile Computing
    "Computing and Remote Access. B/Ds shall define appropriate usage policies and procedures specifying the security requirements when using mobile computing and remote access. Appropriate security measures shall be adopted to avoid unauthorised access to or disclosure of the information stored and processed by these facilities.",
    # Chunk 38: IoT Devices
    "IoT Devices. The acquisition and deployment of IoT devices to process Government information shall be carefully considered and justified. B/Ds shall fully understand the security features of IoT devices before deployment.",
    # Chunk 39: Cryptography Introduction
    "Cryptography. B/Ds shall ensure proper and effective use of cryptography to protect the confidentiality, authenticity and integrity of information.",
    # Chunk 40: Physical Security Introduction
    "Physical and Environmental Security. Careful site selection and accommodation planning of a purpose-built computer installation shall be conducted. Data centres and computer rooms shall have good physical security and strong protection from disaster and security threats.",
    # Chunk 41: Equipment Security
    "Equipment Security. Equipment shall be located properly to minimise risks from environmental hazards. Equipment shall be protected against power failures and other electrical anomalies.",
    # Chunk 42: Operational Procedures
    "Operational Procedures and Responsibilities. Operating procedures shall be documented and made available to all users who need them. Changes to information systems shall be controlled by the use of change control procedures.",
    # Chunk 43: Protection from Malware
    "Protection from Malware. B/Ds shall implement detection, prevention and recovery controls to protect against malware. Users shall be made aware of the risks of malware and the measures they should take.",
    # Chunk 44: Backup Introduction
    "Backup. Backups shall be carried out at regular intervals. B/Ds shall establish and implement backup and recovery policies for their information systems.",
    # Chunk 45: Logging
    "Logging. B/Ds shall produce and keep logs recording user activities, exceptions, faults and information security events. Logging facilities and log information shall be protected against tampering and unauthorised access.",
    # Chunk 46: Technical Vulnerability Management
    "Technical Vulnerability Management. B/Ds shall implement vulnerability management processes, which include identifying, evaluating, mitigating, and tracking of vulnerabilities of their information systems.",
    # Chunk 47: Least Privilege - CORRECT for access control question
    "Least Privilege. B/Ds shall enforce the least privilege principle when assigning resources and privileges of information systems to users. Access to information shall not be allowed unless authorised by the relevant information owners. Access to information systems containing classified information shall be restricted by means of logical access control. Access to classified information without appropriate authentication shall not be allowed.",
    # Chunk 48: User Access Procedures
    "User Access Procedures. Procedures for approving, granting and managing user access, including user registration/de-registration, password delivery and password reset, shall be documented. Data access rights shall be granted to users based on a need-to-know basis. The use of special privileges shall be restricted and controlled. User privileges and data access rights shall be clearly defined and reviewed periodically.",
    # Chunk 49: User Responsibilities
    "User Responsibilities. Users shall be responsible for all activities performed with their user-IDs. Passwords shall not be shared or divulged unless necessary. User shall ensure that unattended equipment has appropriate protection.",
    # Chunk 50: Network Security Management
    "Network Security Management. Networks shall be managed and controlled to protect information in systems and applications. Security mechanisms, service levels and management requirements of all network services shall be identified and included in network services agreements.",
    # Chunk 51: Information Transfer
    "Information Transfer. Formal transfer policies, procedures and controls shall be in place to protect the transfer of information through the use of all types of communication facilities.",
    # Chunk 52: Security Requirements
    "Security Requirements of Information Systems. Information security requirements shall be included in the requirements for new information systems or enhancements to existing information systems.",
    # Chunk 53: Cryptographic Controls - CORRECT for crypto question
    "Cryptographic Controls. B/Ds shall manage cryptographic keys through their whole life cycle, including generating, storing, archiving, retrieving, distributing, retiring and destroying keys. Information classified as RESTRICTED or above shall be encrypted in storage irrespective of the storage media. Information transmitted over networks shall be protected from unauthorised interception and modification by means of encryption.",
    # Chunk 54: Security in Development
    "Security in Development and Support Processes. Rules governing secure software development shall be established and applied to developments within the organisation. Security shall be integrated into the software development life cycle.",
    # Chunk 55: Test Data
    "Test Data. Test data shall be selected carefully, and protected and controlled. Operational data containing personal information shall not be used for testing unless specifically authorised.",
    # Chunk 56: Outsourcing Security
    "Outsourcing Security. IT Security in Outsourcing Service. B/Ds shall ensure that the security controls of outsourced IT services meet the security requirements.",
    # Chunk 57: Cloud Computing - CORRECT for cloud question
    "Cloud Computing Security. Information classified as RESTRICTED or above shall not be stored in or processed by public cloud services. Before signing an agreement with a cloud service provider, B/Ds shall ensure that the shared responsibilities of both parties are clearly defined, documented, and understood.",
    # Chunk 58: Security Incident Management
    "Management of Security Incidents. B/Ds shall establish an incident detection and monitoring mechanism to detect, contain and ultimately prevent security incidents. Staff shall be made aware of the security incident response plan.",
    # Chunk 59: IT Security Continuity
    "IT Security Continuity. B/Ds shall plan for the continuity of IT security during adverse situations, such as during a crisis or disaster. The continuity plan shall be tested regularly.",
    # Chunk 60: Backup Details - CORRECT for backup question
    "Backup and Recovery. Backups shall be carried out at regular intervals. B/Ds shall establish and implement backup and recovery policies for their information systems. Backup activities shall be reviewed regularly. Backup restoration tests shall be conducted regularly. The frequency of backup reviews and restoration tests shall be defined and documented. Backup media should also be protected against unauthorised access, misuse or corruption.",
    # Chunk 61: Compliance
    "Compliance. Compliance with Legal and Contractual Requirements. B/Ds shall ensure compliance with all relevant legislation, regulations and contractual requirements. Security reviews shall be conducted regularly.",
    # Chunk 62: Security Reviews
    "Security Reviews. The implementation of security controls shall be reviewed regularly for compliance with security policies, standards and legal requirements.",
    # Chunk 63: Contact
    "Contact. For enquiries on this document, please contact the Digital Policy Office.",
]

# TUNED TEST QUESTIONS - v2
# These questions match actual S17 policy content with specific implementation details
test_questions = [
    {
        "question": "What are the requirements for managing cryptographic keys?",
        "expected": "B/Ds shall manage cryptographic keys through their whole life cycle including generating, storing, archiving, retrieving, distributing, retiring and destroying keys",
        "correct_doc_id": 53,  # Chunk 53 has specific implementation
        "difficulty": "medium"
    },
    {
        "question": "What is the role of the Departmental IT Security Officer?",
        "expected": "DITSO is appointed from senior management to participate in overall steering of IT security matters and ensure accountability",
        "correct_doc_id": 15,  # Chunk 15 has specific appointment details
        "difficulty": "medium"
    },
    {
        "question": "What are the responsibilities of GIRO?",
        "expected": "GIRO maintains central inventory of incidents, prepares statistics reports, coordinates handling of multiple-point security attacks, and enables experience sharing among ISIRTs",
        "correct_doc_id": 12,  # Chunk 12 has specific GIRO functions
        "difficulty": "hard"  # Multiple docs mention GIRO, need to find right one
    },
    {
        "question": "What is the least privilege principle for access control?",
        "expected": "B/Ds shall enforce least privilege when assigning resources and privileges, granting access only when authorised by information owners",
        "correct_doc_id": 47,  # Chunk 47 has specific 11.1 requirements
        "difficulty": "medium"
    },
    {
        "question": "What are the restrictions for using public cloud services?",
        "expected": "Information classified as RESTRICTED or above shall not be stored in or processed by public cloud services",
        "correct_doc_id": 57,  # Chunk 57 has specific cloud restrictions
        "difficulty": "easy"  # Very specific keyword match
    },
    {
        "question": "What are the requirements for backup and recovery?",
        "expected": "Backups shall be carried out at regular intervals with regular restoration tests and documented frequency",
        "correct_doc_id": 60,  # Chunk 60 has specific 14.3 requirements
        "difficulty": "medium"
    },
]

# Expected behavior by search method:
# - Keyword: Will find "cryptographic", "DITSO", "GIRO" mentions but may rank TOC/docs higher
# - BM25: Better at finding specific policy sections with "shall" requirements
# - Vector: Good at semantic matches but may miss exact policy references
# - Hybrid: Combines both - should find policy sections with right keywords
# - Reranker: Should boost specific implementation docs over overview docs

if __name__ == "__main__":
    print(f"S17 Security Policy Corpus v2")
    print(f"Documents: {len(documents)}")
    print(f"Test questions: {len(test_questions)}")
    print()
    print("Test questions and correct doc IDs:")
    for i, q in enumerate(test_questions):
        print(f"  {i+1}. '{q['question']}' -> Doc #{q['correct_doc_id']} ({q['difficulty']})")
